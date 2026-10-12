"""CT Mode plugin — 会话级 CTF 攻防提示词常驻注入（/ct on | /ct off）。

机制：注册 agent_before hook（agent_loop.py 每个用户轮触发一次）。
当 CT 模式激活时：
  - 激活后的第一轮：把 assets/ct_prompt.md 全文追加到最后一条 user message（一次性注入）；
  - 后续每轮：只追加 ~100 字节的轻量锚点（防止长任务 compaction 后丢失规则锚点），
    避免 56KB 全文每轮重复累积撑爆上下文。
激活态保存在当前 GenericAgent 实例的 _ga_ct_mode_active；各会话互不干扰。
'/ct on' '/ct off' 命令由本插件在 agent_before 中识别并从 user message 中剥离。

依赖文件：assets/ct_prompt.md（CT Attack-Defense Prompt v3.0，触发词：寒霜 / REDBLUE）
"""
import os
import re
import plugins.hooks as hooks

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CT_PROMPT_PATH = os.path.join(_PROJECT_ROOT, 'assets', 'ct_prompt.md')

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
    m = _CMD_RE.search(raw.strip())
    if m:
        _set_ct(ctx, m.group(1).lower() == 'on')
        # 剥离命令本身
        stripped = _CMD_RE.sub('', raw, count=1).strip()
        if isinstance(content, str):
            um['content'] = stripped
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
        if not active:
            return
        # fallthrough：on 的当轮立即注入全文
        handler = ctx.get('handler') if isinstance(ctx, dict) else None
        parent = getattr(handler, 'parent', None)
        prompt = _load_ct_prompt()
        if not prompt:
            _append_text(um, "\n\n---\n[CT MODE] 规则文件缺失: %s\n---" % _CT_PROMPT_PATH)
            return
        _append_text(um, "\n\n---\n[CT MODE] 以下为本项目常驻 CT 攻防规则（全文，仅本轮注入一次）：\n\n" + prompt + "\n---")
        parent._ga_ct_mode_injected = True
        return

    # 2) 激活态注入
    if not _ct_active(ctx):
        return
    handler = ctx.get('handler') if isinstance(ctx, dict) else None
    parent = getattr(handler, 'parent', None)
    injected = getattr(parent, '_ga_ct_mode_injected', False)
    if not injected:
        prompt = _load_ct_prompt()
        if not prompt:
            _append_text(um, "\n\n---\n[CT MODE] 规则文件缺失: %s\n---" % _CT_PROMPT_PATH)
            return
        _append_text(um, "\n\n---\n[CT MODE] 以下为本项目常驻 CT 攻防规则（全文，仅本轮注入一次）：\n\n" + prompt + "\n---")
        parent._ga_ct_mode_injected = True
    else:
        _append_text(um, (
            "\n\n---\n[CT MODE] 激活中。CT 攻防规则全文已在前文注入（含主内核/红队/蓝队/速查表，"
            "触发词：寒霜 / REDBLUE）。若上文已被压缩丢失，请重新读取 %s 并继续遵循。\n---" % _CT_PROMPT_PATH
        ))
