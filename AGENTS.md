# AGENTS.md — AI 协作者工作约定

## 项目
GA（GenericAgent）的 CT 攻防模式插件：`/ct on|off` 会话级提示词常驻注入。

## 硬规则
1. **测试门禁**：改 `src/` 后必须 `./scripts/check.sh` 全绿才可 commit。
2. **只动自己**（决策 D2）：不修改 GA 仓库内 `project_mode.py` 等既有插件；重复代码容忍。
3. **业务变更分离**：bug 修复与行为变更须在 commit message 与 tracker 中显式标注，与纯重构分离。
4. **部署**：`./install.sh` 同步到 GA；GA 重启后生效（插件启动时发现加载）。
5. 问题一律先登记 `docs/exec-plans/tech-debt-tracker.md` 再处理，登记带 `文件:行` 证据。

## 架构速览
`agent_before` hook（每用户轮）→ 命令解析（剥离不发模型）→ 激活轮全文注入 / 后续锚点。激活态 = Agent 实例属性。详见 `docs/ARCHITECTURE.md`。

## 当前状态
B1-B4 完成（git 化 / 测试 / 重构 / 文档）。遗留 P2 见 tracker。
