# ARCHITECTURE — ct_mode 插件

## 组件
```
GenericAgent 宿主
 └─ plugins/hooks.py: discover_and_load() → import ct_mode → @hooks.register('agent_before')
     ↓ 每个用户轮触发 ct_mode(ctx)
        ctx = {messages: [...], handler: (其 .parent = Agent 实例)}
```

## 数据流（每用户轮）
1. `_find_last_user_message(ctx)` → um（无则返回）
2. 提取文本（str 或 list 中首个 text block）
3. `_handle_command`：匹配 `/ct on|off`（大小写/空白容错）→ 写激活态到 `parent._ga_ct_mode_active`、从 um 剥离命令 → on 则当轮 `_inject_full_prompt`
4. 非命令且已激活：`_ga_ct_mode_injected` 未标记 → 全文；已标记 → `_inject_anchor`（148B，含 ct_prompt.md 路径指针，抗 compaction）
5. 未激活：直接返回（零注入）

## 状态（均在 Agent 实例上，会话隔离）
| 属性 | 含义 |
|---|---|
| `_ga_ct_mode_active` | 激活开关 |
| `_ga_ct_mode_injected` | 全文是否已注入过（防重复膨胀） |

## 边界与降级
- 规则文件缺失：每轮注入"缺失"提示，不标记 injected（诚实重试）
- handler/parent 异常结构：getattr 防御，注入状态丢失仅退化为重复注入，不崩
- 无宿主独立运行（测试）：import 容错 stub，register no-op

## 已知取舍
- 锚点每轮 ~148B 线性累积（10 轮约 1.5KB）——豁免，见 tracker TD-PERF-001
- 与 project_mode.py 存在模式性重复——D2 决策容忍，不动他人插件
