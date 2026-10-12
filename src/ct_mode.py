"""CT Mode plugin — 会话级 CTF 攻防提示词常驻注入（/ct on | /ct off）。

机制：注册 agent_before hook（agent_loop.py 每个用户轮触发一次）。
当 CT 模式激活时：
  - 激活后的第一轮：注入「主内核+速查表」(assets/ct_prompt_kernel.md) + 强装载指引；
    红队块/蓝队块不预注入，由模型按 §1.2 方向判定后自行 file_read（A 方案）；
  - 后续每轮：只追加 ~100 字节的轻量锚点（防止长任务 compaction 后丢失规则锚点），
    首轮注入约 38KB（原全卷 56KB），方向块按需读取。
激活态保存在当前 GenericAgent 实例的 _ga_ct_mode_active；各会话互不干扰。
'/ct on' '/ct off' 命令由本插件在 agent_before 中识别并从 user message 中剥离。

依赖文件：assets/ct_prompt_kernel.md（主内核+速查表）、assets/ct_prompt_red.md（红队块）、assets/ct_prompt_blue.md（蓝队块）
（旧 assets/ct_prompt.md 全卷文件保留，不再作为注入源）
"""
import os
import re
try:
    import plugins.hooks as hooks
except ImportError:  # 独立测试/无宿主环境：提供 no-op stub
    class _HooksStub:
        @staticmethod
        def register(event):
            return lambda fn: fn  # 装饰器工厂 no-op
    hooks = _HooksStub()

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CT_PROMPT_PATH = os.path.join(_PROJECT_ROOT, 'assets', 'ct_prompt_kernel.md')
_RED_PATH = os.path.join(_PROJECT_ROOT, 'assets', 'ct_prompt_red.md')
_BLUE_PATH = os.path.join(_PROJECT_ROOT, 'assets', 'ct_prompt_blue.md')

_CMD_RE = re.compile(r'^\s*/ct\s+(on|off)\s*$', re.IGNORECASE)


def _ct_active(ctx=None):
    """返回当前 Agent 实例 CT 模式是否激活。"""
    handler = ctx.get('handler') if isinstance(ctx, dict) else None
    parent = getattr(handler, 'parent', None)
    return bool(getattr(parent, '_ga_ct_mode_active', False))


def _set_ct(ctx, value):
    handler = ctx.get('handler') if isinstance(ctx, dict) else None
    parent = getattr(handler, 'parent', None)
    if parent is not None:
        parent._ga_ct_mode_active = bool(value)
        if value:
            parent._ga_ct_mode_injected = False  # 重置：激活后下一轮做全文注入


def _load_ct_prompt():
    if not os.path.isfile(_CT_PROMPT_PATH):
        return None
    with open(_CT_PROMPT_PATH, encoding='utf-8') as f:
        return f.read()


def _find_last_user_message(ctx):
    return next((m for m in reversed(ctx.get('messages') or [])
                 if isinstance(m, dict) and m.get('role') == 'user'), None)


def _append_text(um, text):
    content = um.get('content')
    if isinstance(content, str):
        um['content'] = content + text
    elif isinstance(content, list):  # 多模态：追加 text block
        content.append({'type': 'text', 'text': text})


def _get_parent(ctx):
    """从 hook ctx 中防御性取出 Agent 实例（handler.parent）。"""
    handler = ctx.get('handler') if isinstance(ctx, dict) else None
    return getattr(handler, 'parent', None)


def _inject_full_prompt(um, parent):
    """注入主内核+速查表+强装载指引（激活后首次），成功返回 True。"""
    prompt = _load_ct_prompt()
    if not prompt:
        _append_text(um, "\n\n---\n[CT MODE] 规则文件缺失: %s\n---" % _CT_PROMPT_PATH)
        return False
    directive = (
        "\n\n=== [CT MODE] 方向块装载指引（最高优先级，必须遵守）===\n"
        "主内核已注入。红队块 (%s) 与蓝队块 (%s) 未预载。\n"
        "硬约束：在你产出任何交付物（PoC/报告/方案/复盘）之前，必须先按主内核 §1.2 判定任务方向，\n"
        "并用 file 工具读取对应方向块——攻击/拿flag/渗透 → 红队块；防御/加固/应急响应 → 蓝队块；\n"
        "AWD 或混合任务 → 两块都读。读取后方可继续。禁止在未读取方向块的情况下产出交付物。\n"
        "=== 指引结束 ===\n" % (_RED_PATH, _BLUE_PATH)
    )
    _append_text(um, "\n\n---\n[CT MODE] 以下为本项目常驻 CT 攻防规则（主内核+速查表，仅本轮注入一次）：\n\n" + prompt + directive + "\n---")
    if parent is not None:
        parent._ga_ct_mode_injected = True
    return True


def _inject_anchor(um):
    """后续轮轻量锚点：提示规则已注入 + 抗 compaction 的文件指针。"""
    _append_text(um, (
        "\n\n---\n[CT MODE] 激活中。主内核+速查表已在前文注入；红队块 %s、蓝队块 %s "
        "须按方向判定用 file 工具自行读取（交付前必读，触发词：寒霜 / REDBLUE）。"
        "若上文已被压缩丢失，请重新读取 %s 并继续遵循。\n---" % (_RED_PATH, _BLUE_PATH, _CT_PROMPT_PATH)
    ))


def _handle_command(um, content, raw, ctx):
    """处理 /ct on|off：设置激活态、剥离命令、当轮注入全文（on 时）。"""
    m = _CMD_RE.search(raw.strip())
    if not m:
        return False
    _set_ct(ctx, m.group(1).lower() == 'on')
    # 剥离命令本身（str 直接改；list 找最后一个含命令的 text block）
    if isinstance(content, str):
        um['content'] = _CMD_RE.sub('', raw, count=1).strip()
    else:
        for b in reversed(content):
            if isinstance(b, dict) and b.get('type') == 'text' and _CMD_RE.search(b.get('text', '').strip()):
                b['text'] = _CMD_RE.sub('', b['text'], count=1).strip()
                break
    active = _ct_active(ctx)
    _append_text(um, (
        f"\n\n---\n[CT MODE] {'已激活' if active else '已退出'}。"
        + ("规则全文将在本轮注入。" if active else "后续轮不再注入 CT 规则。")
        + "\n---"
    ))
    if active:
        _inject_full_prompt(um, _get_parent(ctx))
    return True


@hooks.register('agent_before')
def ct_mode(ctx):
    """每个用户轮起始：解析 /ct on|off 命令；激活态按轮注入全文或轻量锚点。"""
    um = _find_last_user_message(ctx)
    if um is None:
        return
    content = um.get('content')
    raw = content if isinstance(content, str) else next(
        (b.get('text', '') for b in content
         if isinstance(b, dict) and b.get('type') == 'text'), '')
    if not isinstance(raw, str):
        return

    # 1) 命令解析：/ct on | /ct off（从 user message 剥离，不发给模型）
    if _handle_command(um, content, raw, ctx):
        return

    # 2) 激活态注入
    if not _ct_active(ctx):
        return
    parent = _get_parent(ctx)
    if getattr(parent, '_ga_ct_mode_injected', False):
        _inject_anchor(um)
    else:
        _inject_full_prompt(um, parent)
