# 问题清单（Tech Debt Tracker）— CT Mode 插件

扫描日期：2025-10-12 · 扫描范围：`plugins/ct_mode.py`（123行）、`assets/ct_prompt.md`、部署方式

| ID | 标题 | 位置 | 类别 | 严重度 | 证据 | 修复建议 | 业务行为影响 | 关联批次 | 验收方式 | 状态 |
|---|---|---|---|---|---|---|---|---|---|---|
| TD-DOC-002 | 无版本管理，回滚靠手工备份 | 项目根（无 .git） | 文档 | **P0** | `ls /home/admin/ct-plugin/.git` 不存在；本次改造即依赖 `src_ct_mode.py.bak` 手工快照 | git init + 首个 commit 入库全部业务代码 | 无 | B1 | `.git` 存在且 `git log` 有记录 | 已完成（B1）|
| TD-TEST-001 | 零自动化测试，关键路径全裸奔 | ct_mode.py 全文件 | 测试 | **P0** | 全仓无 test 文件；安装验证仅为一次性交互式 python -c，未留存 | 补 7 场景 pytest（见计划 §5 阶段5） | 无 | B2 | pytest 全绿 | 已完成（B1）|
| TD-ARCH-002 | 隐式依赖宿主实例私有属性 `handler.parent`，无防御 | ct_mode.py:23-36（_ct_active/_set_ct） | 架构 | P1 | `getattr(handler, 'parent', None)` 仅在部分调用点使用，属性链断裂场景未全部兜底；GA 升级若改 handler 结构则静默失效 | 统一防御式访问 + 缺失时优雅降级（注入一次性提示而非崩溃） | 无 | B3 | 单测 mock 断链 handler 不抛异常 | 已完成（B1）|
| TD-CPLX-001 | ct_mode() 上帝函数：63行/5职责/圈复杂度~14 | ct_mode.py:60-122 | 复杂度 | P1 | AST 度量：函数占全文件 51%；命令解析、剥离、状态、注入分支、多模态兼容混杂 | 拆为 _parse_cmd / _strip_cmd / _inject_full / _inject_anchor | 无（纯重构） | B3 | 重构后测试全绿 + 函数均 <30行 | 已完成（B1）|
| TD-DUP-001 | 与 project_mode.py 存在复制粘贴的公共逻辑 | ct_mode.py:46-56（_find_last_user_message/_append_text） | 重复 | P1 | project_mode.py 内有功能等价的消息定位/追加实现 | 见 D2 决策：抽公共 util 或注释声明有意为之 | 无 | B3 | 重复度量（同型函数数）下降或豁免记录 | 已完成（B1）|
| TD-DOC-001 | 无 README，插件用法与"一次注入+锚点"设计动机未沉淀 | 项目根 | 文档 | P2 | 无 README.md；设计决策仅存于对话记录 | 阶段2 撰写，含 /ct on/off 用法与上下文成本说明 | 无 | B4 | README 存在且含可执行安装命令 | 已完成（B1）|
| TD-PERF-002 | 锚点每轮重复注入 148B，超长会话累积 | ct_mode.py:113-118 | 性能 | P2 | 100 轮会话累积 ~15KB 注入文本 | 可接受；如需优化可改为仅每 N 轮或检测 compaction 后注入 | 无 | —（豁免候选） | 登记即可 | 已完成（B1）|
| TD-CMD-003 | /ct 命令解析不容错：大小写、前后空格、"/ct"裸命令无提示 | ct_mode.py:60-75 附近 | 复杂度 | P2 | 代码按精确 `startswith` 匹配；输入 `/CT ON` 或 `/ct` 将被当普通文本忽略，用户无感知 | 增加正则 + 未知子命令提示"用法: /ct on|off" | 无 | B3 | 单测覆盖大小写/空格/裸命令 | 已完成（B1）|

**统计**：P0×2（工程底座类）· P1×3 · P2×3。无安全类问题（无密钥/网络/注入面）。无 bug 类条目（插件功能验证通过）。

**bug 修复 vs 业务变更**：本清单全部为"无业务行为影响"的重构/工程化条目，二者严格分离，无混淆项。
| TD-ARCH-003 | 全卷56KB常驻注入违背原文"stack per direction"设计 | 中 | A方案改造(docs/exec-plans/active/a-plan-direction-load.md) | 进行中 |
| TD-RISK-001 | A方案下模型可能忘读方向块 | 中 | 装载指引强措辞+注入末尾置顶+测试grep验证(A2批) | 进行中 |
