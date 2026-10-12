"""ct_mode.py 单元测试 —— 覆盖 7 个核心场景（对应 TD-TEST-001 验收标准）。

运行: python -m pytest tests/ -v
无需真实 GA 宿主：用 stub 模拟 handler/parent/messages。
"""
import importlib.util
import os
import sys

import pytest

_SRC = os.path.join(os.path.dirname(__file__), "..", "src", "ct_mode.py")


def load_ct_mode(tmp_path, prompt_text="# CT RULES ...fake full prompt for test"):
    """把 ct_mode.py 加载为独立模块，并把规则文件指向临时文件。"""
    pfile = tmp_path / "ct_prompt.md"
    pfile.write_text(prompt_text, encoding="utf-8")
    spec = importlib.util.spec_from_file_location("ct_mode_under_test", _SRC)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["ct_mode_under_test"] = mod
    spec.loader.exec_module(mod)
    mod._CT_PROMPT_PATH = str(pfile)
    return mod


class FakeParent:
    pass


class FakeHandler:
    def __init__(self):
        self.parent = FakeParent()


def run(mod, text, handler):
    msgs = [{"role": "user", "content": text}]
    mod.ct_mode({"messages": msgs, "handler": handler})
    return msgs[0]["content"]


# ── 场景 1: /ct on 激活，当轮注入全文 + 剥离命令 ──────────────
def test_ct_on_injects_full_prompt_once(tmp_path):
    mod = load_ct_mode(tmp_path)
    h = FakeHandler()
    out = run(mod, "/ct on", h)
    assert "CT RULES" in out and "fake full prompt" in out
    assert "/ct" not in out
    assert getattr(h.parent, "_ga_ct_mode_active", False) is True
    assert getattr(h.parent, "_ga_ct_mode_injected", False) is True


# ── 场景 2: 激活后普通轮只注入轻量锚点（不重复全文）────────────
def test_subsequent_round_anchor_only(tmp_path):
    mod = load_ct_mode(tmp_path)
    h = FakeHandler()
    run(mod, "/ct on", h)
    out2 = run(mod, "处理这道Web题", h)
    assert "激活中" in out2 and "CT RULES" not in out2
    assert len(out2) < 400  # 锚点必须轻量


# ── 场景 3: /ct off 退出后零注入 ─────────────────────────────
def test_ct_off_stops_injection(tmp_path):
    mod = load_ct_mode(tmp_path)
    h = FakeHandler()
    run(mod, "/ct on", h)
    out = run(mod, "/ct off", h)
    assert "已退出" in out and "/ct" not in out
    assert getattr(h.parent, "_ga_ct_mode_active", False) is False
    plain = run(mod, "普通问题", h)
    assert plain == "普通问题"


# ── 场景 4: 未激活时普通消息完全不注入 ────────────────────────
def test_inactive_noop(tmp_path):
    mod = load_ct_mode(tmp_path)
    out = run(mod, "普通问题", FakeHandler())
    assert out == "普通问题"


# ── 场景 5: 会话隔离——两个 parent 互不干扰 ────────────────────
def test_session_isolation(tmp_path):
    mod = load_ct_mode(tmp_path)
    h1, h2 = FakeHandler(), FakeHandler()
    run(mod, "/ct on", h1)
    out2 = run(mod, "另一个会话的问题", h2)
    assert "CT RULES" not in out2  # h2 未激活，不注入


# ── 场景 6: 规则文件缺失时不崩溃，注入错误提示 ────────────────
def test_missing_prompt_file_graceful(tmp_path):
    mod = load_ct_mode(tmp_path)
    mod._CT_PROMPT_PATH = str(tmp_path / "not_exist.md")
    h = FakeHandler()
    out = run(mod, "/ct on", h)
    assert "缺失" in out
    out2 = run(mod, "继续干活", h)  # 后续轮也不崩；文件仍缺失则每轮诚实提示（不能谎称"已注入"）
    assert "缺失" in out2


# ── 场景 7: 多模态 list 消息同样可注入 ────────────────────────
def test_multimodal_list_message(tmp_path):
    mod = load_ct_mode(tmp_path)
    h = FakeHandler()
    msgs = [{"role": "user", "content": [
        {"type": "text", "text": "/ct on"},
        {"type": "image_url", "image_url": {"url": "x"}},
    ]}]
    mod.ct_mode({"messages": msgs, "handler": h})
    texts = [b for b in msgs[0]["content"] if b["type"] == "text"]
    assert any("CT RULES" in b["text"] for b in texts)
