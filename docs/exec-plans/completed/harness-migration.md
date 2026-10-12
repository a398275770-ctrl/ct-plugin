# Harness 工程化改造计划 — CT Mode 插件

## 0. 元信息
- 项目 / 仓库：GA ct_mode 插件（业务代码位于 `/home/admin/GenericAgent/plugins/ct_mode.py` + `/home/admin/GenericAgent/assets/ct_prompt.md`；本项目根 `/home/admin/ct-plugin` 承载文档与计划）
- 分支：harnessing（当前无 git 仓库，见 TD-DOC-001）
- 计划版本 / 日期：v1.0 / 2025-10-12
- 状态：**已完成**

## 1. 项目概况
- 技术栈：Python 3（单文件插件，无第三方依赖），宿主为 GenericAgent 插件系统（`plugins/hooks.py` 的 discover_and_load 自动发现 + `agent_before` 事件）
- 构建/运行方式：GA 启动时自动 import；无独立构建产物；无部署流程（文件即部署）
- 入口点：`ct_mode()`（agent_before hook 回调），命令 `/ct on` `/ct off`，激活态存于 Agent 实例属性 `_ga_ct_mode_active`
- 顶层模块：`src_ct_mode.py.bak`（业务代码快照，123 行，6 个函数，最大函数 ct_mode 63 行）
- 测试现状：**无任何自动化测试**，仅有本次安装时的一次性手工模拟验证（hooks.trigger 三轮验证，未留存为脚本）
- CI 现状：无

## 2. 框架判定与 CI 现状（见 §3.2）
- 判定结果：**其他**（纯 Python 宿主插件，非 Tauri）
- 判定证据：`ct_mode.py` 全文为 Python；无 package.json / tauri.conf.json / 前端构建链
- 现有 .github/workflows/：无
- 发布链路现状：手工 cp 文件部署到 GA 目录，无版本化

## 3. 现状诊断

### 3.1 架构现状（模块依赖图）
```
plugins/hooks.py (宿主) ──discover_and_load──> ct_mode.py
ct_mode.py ──读取──> assets/ct_prompt.md (56KB 规则文件)
ct_mode.py ──mutate──> ctx['messages'][-1]（最后一条 user message）
ct_mode.py ──读写──> handler.parent._ga_ct_mode_active / _ga_ct_mode_injected（实例属性）
```
- 无循环依赖；但与宿主存在**隐式契约依赖**（见 TD-ARCH-002：依赖 `handler.parent` 私有属性路径，宿主重构即碎）

### 3.2 复杂度热点
- `ct_mode()` 函数 63 行（占全文件 51%），承担：命令解析 + 剥离 + 状态读写 + 全文/锚点注入分支 + 多模态兼容 5 种职责，圈复杂度估算 ~14。属"上帝函数"苗头（TD-CPLX-001）

### 3.3 重复代码
- `_append_text` / `_find_last_user_message` 与 `project_mode.py` 中同名逻辑高度相似（插件间复制粘贴，TD-DUP-001）
- 锚点文案中文件路径硬编码重复出现 2 处

### 3.4 文档缺口
- 无 README（TD-DOC-001）；插件行为（会话级隔离、一次注入+锚点设计原因）只存在于对话记录，未沉淀
- 无 git 仓库，无变更历史，回滚靠手工备份（TD-DOC-002，P0）

### 3.5 测试缺口
- 零自动化测试。关键路径全部未测：/ct 命令解析边界（大小写、前后空格、/ct 不带参数）、多模态 list content 分支、规则文件缺失分支、多会话隔离、compaction 后锚点恢复（TD-TEST-001，P0）

### 3.6 安全与性能风险
- 性能：每次激活轮同步读 56KB 文件（可接受，仅一次）；但**锚点轮每轮重复注入 148B**，超长会话（>100轮）累积 ~15KB，可接受但需登记（TD-PERF-002）
- 安全：无密钥、无网络、无注入面。唯一风险是 ct_prompt.md 内容本身作为提示词注入——属产品预期行为，非漏洞。**无 P0 安全项**

## 4. 改造批次划分
| 批次 | 覆盖业务域 | 主要目标 | 依赖前置 | 回滚方案 |
|---|---|---|---|---|
| B1 | 工程底座 | git init + README + 代码入库 + 安装脚本 | 无 | 删仓库即可，业务代码不受影响（文件级回滚） |
| B2 | 测试补全 | pytest 化的 hook 模拟测试（6 个场景，见 §5 阶段5） | B1 | 测试文件独立，删除即回滚 |
| B3 | 重构 | ct_mode() 拆分 + 消除与 project_mode 重复（抽公共 util 或各自保留并注释） | B2（有测试保护才敢动） | git revert 单 commit |
| B4 | 文档对齐 | AGENTS.md/ARCHITECTURE.md + docs/CI.md | B1 | 文档独立提交 |

## 5. 五阶段任务拆解

### 阶段 1 · 全量扫描与问题清单（本次已完成）
- 产出物：本文档 + `docs/exec-plans/tech-debt-tracker.md`
- 验收：问题条目均含 文件:行 证据；未改业务代码（见 §7 自证）

### 阶段 2 · 文档对齐
- 子任务：README（安装/用法/设计说明）、AGENTS.md、ARCHITECTURE.md（含依赖图 §3.1 落地）
- 验收标准（可机械检查）：README 含可复制执行的安装命令；ARCHITECTURE 中依赖图与 `grep -n "import" ct_mode.py` 实际一致

### 阶段 3 · 门禁审计与自动化质量校验
- 子任务：pre-commit（ruff lint + py_compile）；CI 仅本地脚本（`scripts/check.sh`），GitHub Actions 不适用（项目不在 GitHub）
- 三问：无 API 变更面（插件对宿主是事件回调）；无数据迁移；无 UI
- 验收：`scripts/check.sh` 一键全绿；任何 py 语法错误被拦截

### 阶段 4 · 问题修复与重构（批次 B3）
- 子任务：TD-CPLX-001 拆函数、TD-DUP-001 消重、TD-ARCH-002 加 getattr 防御
- 验收：重构前后测试全绿（B2 用例即对拍基准）；git diff 仅限插件文件

### 阶段 5 · 测试补全与门禁接入
- 测试场景清单：①/ct on 当轮全文注入 ②后续轮仅锚点 ③/ct off 后零注入 ④命令大小写/空格容错 ⑤多模态 list content ⑥规则文件缺失降级 ⑦双实例会话隔离
- 验收：pytest 覆盖上述 7 场景；`scripts/check.sh` 串联 lint+test

## 6. 待人工决策清单
| 编号 | 问题 | 为什么需要人判断 | 影响范围 |
|---|---|---|---|
| D1 | 仓库位置：在 `/home/admin/ct-plugin` 建独立 git 仓库，还是把 GA 仓库整体 git 化 | GA 仓库归属权/是否允许 git init 由你决定 | B1 |
| D2 | 与 project_mode.py 的重复代码：抽公共模块（改 GA 另一插件，风险外溢）vs 只在 ct_mode 内重构（保守） | 涉及改动他人/既有插件，风险偏好问题 | B3 |
| D3 | 部署方式：维持手工 cp，还是写 install.sh 从本仓库同步到 GA 目录 | 使用习惯问题 | B1 |

## 7. 进度与决策日志
| 日期 | 阶段 | 动作 | 关联 commit | 决策与理由 |
|---|---|---|---|---|
| 2025-10-12 | 1 | 全量扫描完成，产出本计划与问题清单 | 无（尚无 git） | 按规则只登记不修；框架判定"其他"，无 Tauri 询问必要 |
