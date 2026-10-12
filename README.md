# CT Mode — GenericAgent 会话级 CTF 攻防提示词插件

## 是什么
GA 插件，一条命令让整份 CT 攻防提示词（56KB）在本会话常驻注入，退出即失效。会话间隔离。

## 用法
```bash
/ct on    # 项目开始时：当轮注入规则全文，后续轮仅 ~150B 锚点
/ct off   # 结束：后续零注入
```
命令不区分大小写，可带前后空格。运行中的 GA 需重启后新插件才被发现。

## 一键安装

### Linux / macOS
```bash
curl -fsSL https://raw.githubusercontent.com/a398275770-ctrl/ct-plugin/main/remote-install.sh | sh
```
GA 装在别处：`GA_ROOT=/路径` 加在命令前面。

### Windows (PowerShell)
```powershell
irm https://raw.githubusercontent.com/a398275770-ctrl/ct-plugin/main/remote-install.ps1 | iex
```
GA 装在别处：先执行 `$env:GA_ROOT="D:\GenericAgent"`。

装完重启 GA，在会话中输入 `/ct on` 即可启用。
> 两种方式都自动完成：克隆到 `~/ct-plugin` → 运行测试 → 部署到 GA（要求机器已装 git 和 python3）。

## 已装过，更新（一键）

```bash
cd ~/GenericAgent && ./update-ct          # Linux/macOS，在 GA 目录直接敲
# Windows: powershell -ExecutionPolicy Bypass -File $HOME\ct-plugin\update.ps1
```

## 开发
```bash
./scripts/check.sh         # 语法 + pytest 7 场景
python3 -m pytest tests/ -v
```

## 目录
```
src/ct_mode.py      插件本体（宿主 GA 自动发现加载）
src/ct_prompt.md    攻防提示词全文（触发词：寒霜 / REDBLUE）
tests/              7 场景：激活/锚点/退出/未激活/会话隔离/文件缺失/多模态
docs/               改造计划、问题清单、架构说明
```

## 设计要点
- **一次全文 + 轻量锚点**：56KB 只在激活轮注入一次；后续每轮仅注入 148B 锚点（含文件指针，compaction 后可自恢复），避免上下文爆炸。
- **会话隔离**：激活态存于 Agent 实例 `_ga_ct_mode_active`，多会话互不干扰。
- **诚实降级**：规则文件缺失时每轮明示"缺失"，绝不谎称已注入。

## 维护约定（对 AI 协作者）
改 `src/ct_mode.py` 前先跑 `./scripts/check.sh`；commit 前 7 测试必须全绿；每个批次独立 commit 可回滚。问题登记见 `docs/exec-plans/tech-debt-tracker.md`。
