# CT Mode — GenericAgent 会话级 CTF 攻防提示词插件

## 是什么
GA 插件，一条命令让整份 CT 攻防提示词（56KB）在本会话常驻注入，退出即失效。会话间隔离。

## 用法
```bash
/ct on    # 项目开始时：当轮注入规则全文，后续轮仅 ~150B 锚点
/ct off   # 结束：后续零注入
```
命令不区分大小写，可带前后空格。运行中的 GA 需重启后新插件才被发现。

## 三步上手（新电脑）
```bash
# 1. 克隆（首次需在新机器配置你自己的 GitHub SSH key）
git clone git@github.com:a398275770-ctrl/ct-plugin.git && cd ct-plugin
# 2. 安装到 GA
./install.sh
# 3. 重启 GA，然后在会话里输入: /ct on
```

## 已装过，只想要最新版（一键，两种任选）
```bash
cd /home/admin/GenericAgent && ./update-ct   # 在 GA 目录里直接敲
# 或
cd ct-plugin && ./update.sh
```
> `GA_ROOT=/你的GA路径 ./install.sh` 可覆盖默认部署目录

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
