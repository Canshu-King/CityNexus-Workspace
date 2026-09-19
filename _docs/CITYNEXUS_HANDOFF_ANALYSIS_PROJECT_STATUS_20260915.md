# CityNexus 交接文件：给下一个 GPT / Codex 窗口

> 生成时间：2026-09-13（Asia/Shanghai）  
> 来源任务：`完善 Codex 铺路 乐彩`  
> 来源 conversation id：`6aa1f9e6-23c0-83ea-9555-e6fd2d78e180`  
> 当前工作区假设：`D:\moodle\CityNexus`

## 0. 使用说明

这是一份从上一窗口长上下文中提炼出的交接资料，不是当前仓库的最终真相。下一个 GPT 必须先检查真实工作树、代码、测试和最近的 diff；历史报告中的 `PASS`、`IMPLEMENTED`、`FROZEN` 只能当线索，不能直接当验收结论。

本文件刻意不包含历史对话里出现过的任何 API Key。此前曾使用过临时、低额度的 DeepSeek Key 和 21st.dev Key；不要从旧聊天、日志或压缩包中复制密钥，也不要把密钥写入仓库。只允许通过运行时环境变量提供：

```powershell
$env:DEEPSEEK_API_KEY = "<runtime secret>"
$env:API_KEY_21ST = "<runtime secret>"
```

代码、日志、Markdown、Git diff、测试输出和最终 checkpoint 只能出现变量名，不能出现真实值。历史密钥已经在聊天中暴露过，完成实机验证后应视为需要撤销/轮换的临时凭证。

---

## 1. 项目身份和最终产品愿景

课程题目是 **#11 A Smart City Traveler System**，产品名为 **CityNexus**。

CityNexus 不是普通旅游攻略、地图壳、AI 聊天框或景点推荐器。核心产品问题是 **Journey Continuity**：

> 当天气、交通、营业状态、预约和用户实际执行进度不断变化时，系统能否持续知道整趟旅程是否仍然成立，并在用户授权范围内保护关键承诺、恢复剩余行程。

终局定位：

> 一个主动感知城市现实、维护 Journey 数字孪生，并在用户授权范围内自主调整和执行整趟 Journey 的智能城市旅程代理系统。

产品生命周期已经确定为：

```text
Discover → Compose → Commit → Execute → Recover → Reflect
```

### 核心领域对象

- `Journey`：用户整趟旅程的聚合。
- `PlanVersion`：旅程的具体计划版本。重新规划不得覆盖旧计划；应为旧版本标记 `SUPERSEDED`，新版本标记 `ACTIVE`。
- `Activity`：计划中的具体活动。
- `Commitment`：由预约、付款或现实承诺形成的不可随意破坏的约束；尤其是 C4 / locked / paid commitment。
- `JourneyTwin`：面向读取的投影，不是事实源。它应从持久化领域实体投影 `ACTIVE PlanVersion`、执行指针、下一活动、Commitment、预算、机会窗口、交通/天气/provider 状态和重规划状态。
- `MobilitySnapshot`：一次操作所冻结的交通事实集合，必须可审计、可重放、不可被内部字典偷偷修改。
- `ExecutionClock`：Journey 时区下统一的真实“现在”，驱动 `NOW`、`NEXT`、`LEAVE BY`、C4 倒计时、Offline、Push 和 PIC。

不可破坏的权威边界：

```text
Provider 负责提供事实，不负责裁判
DeepSeek/Hermes 负责理解、推理、候选和编排，不直接改数据库
OR-Tools 负责候选排程，不是最终事实裁判
CityNexus deterministic layer 负责领域事实、硬约束和最终可行性
Gateway / Delegation Policy 负责判断 Agent 是否有权执行
```

---

## 2. 现在真正应该相信的成熟度

上一轮 V11 最重要的结论不是“全部完成”，而是：基础已经很强，但若干能力仍被报告过度宣称。下表是外部审查后的真实口径。

| 能力 | 当前真实判断 | 交接时的处理 |
|---|---|---|
| Journey / PlanVersion / JourneyTwin 基础 | 基本冻结 | 只做回归，不要推翻 |
| Backend-connected Vertical Slice | 已形成可信闭环 | 作为回归锚点保留 |
| DeepSeek Responses tool loop | 高可信 PASS；缺少机器可重放的脱敏 trace | 补 `AgentRun/tool trace` 证据 |
| Agent Principal / Gateway / Policy | 基础很强 | 继续验证 approval、身份和幂等 |
| Provider-backed sequential compose | 可用 | 不要称为真正多日 Compose |
| Frozen Evidence Select Gate | **P0，未完成** | Compose 与 Select 必须复用同一证据 |
| Real multi-day Compose | **未完成** | V12 最大产品任务之一 |
| ExecutionClock | 已修复并在 Edge/Offline 使用 | 继续接入所有 NOW/NEXT 视图 |
| Execution state machine | **部分完成** | 补 `NOT_STARTED/EN_ROUTE/ARRIVED/IN_PROGRESS` |
| DnD Trip Studio | 交互基础存在，实际编辑 **部分完成** | 拖拽后必须走 Preview/Replan/Impact/Accept |
| Money semantics | **部分完成** | `UNKNOWN` 不得变成金额 0 |
| MapLibre | 已接入但桌面 resize 未完成 | 加 `ResizeObserver → map.resize()` |
| Storybook design system | 只有少量 stories | 扩充组件和状态矩阵 |
| OpenAPI typed client | 生成类型已出现但使用不完整 | 继续替换手写 type/fetch |
| SearXNG Sourceful runtime | 只有 adapter 基础 | 不要称为完整 Web intelligence |
| 包卫生 / 进度报告 | V11 仍有 cache/pyc，进度记录不完整 | 最终 fresh-extract、secret scan、卫生检查 |

### V11 已经确认的关键问题

1. **Select 又抓了新 Provider 世界。** Generic Compose 先得到 Snapshot A，Select 时用 `selection-gate` 再抓 Snapshot B；Plan explanation 只有摘要，没有可恢复的完整 frozen evidence。必须在 `PlanVersion` 中保存 `mobility_snapshot_id`，并持久化 facts、geometry、provider、capture time、provenance、degraded/fallback 信息。Compose、Select、Reload、Map、JourneyTwin 都指向同一份权威证据。
2. **Generic Compose 仍按用户输入顺序串行排列。** 目前能接受任意 POI，但还不能联合决定 Day、顺序、住宿、Arrival/Departure、既有预约、交通方式和预算。
3. **DnD 拖完基本只记录 `console.info("pending-feasibility")`。** 还没有真正的 provider 重算、时间/费用/C4 buffer 影响预览和 Accept 后的新 `PlanVersion`。
4. **执行状态仍主要是 `ACTIVE/COMPLETED/SKIPPED`。** 没有完整的正在出发、在路上、已到达、活动进行中状态。
5. **`UNKNOWN` 金额可能被 `int(price or 0)` 转成 0。** “不知道”不等于“免费”，应引入 `MoneyEvidence`，至少区分 `FREE_KNOWN / KNOWN / ESTIMATED / UNKNOWN`，未知时 `amount = null`。
6. **MapLibre 没有 ResizeObserver。** 左栏、AI drawer、窗口尺寸变化后要调用 `map.resize()`。
7. **Storybook、OpenAPI、Sourceful Search、交付包卫生仍是部分完成。** 不要用库已安装、adapter 已存在或截图好看来替代真实 E2E。

---

## 3. 之前已经形成的可信回归锚点

不要无理由重写这一条 Golden Scenario。它是后续 Provider、Solver、AI 和前端工作的基础：

```text
Demo reset
→ Generate Plan
→ Select Plan
→ Book River Cruise
→ CAPTURE payment
→ 形成 durable C4 Commitment
→ Start Journey
→ 完成前置 Activity
→ current Activity = Tech Art Center
→ 13:25 Closure Event
→ Generate multiple Replan proposals
→ F3 使用 Event time 和真实 current Activity 作为起点
→ deterministic feasibility
→ 保留 River Cruise C4
→ Accept proposal
→ old PlanVersion = SUPERSEDED
→ new PlanVersion = ACTIVE
→ C4 activity_id remap 到新 Plan
→ JourneyTwin refresh
→ browser reload
→ 状态仍从 Backend Truth 恢复
```

历史审查中，这条链曾在不同 checkpoint 达到 `155 passed / 1 skipped`、`157 passed / 1 skipped` 等结果；Provider/Weather 后续阶段也曾报告 `170/1`、`194/1` 等。数字属于历史证据，下一窗口必须以当前工作树重新运行的结果为准。

---

## 4. V12 主目标：Authoritative Trip Composition & Live Journey Execution

V12 不再是“再添加十几个 interface”。完成标准是：

> 同一趟真实/捕获旅行，从规划、选择、拖拽修改、开始执行、途中变化、AI 恢复，到手机、Offline、Map、JourneyTwin、PIC 和 Guardian，所有界面看到的是同一个世界。

### V12 四个主支柱

#### A. Persisted Provider Evidence / Same-world Select Gate

目标链路：

```text
Provider capture
→ Frozen Mobility Evidence
→ Compose
→ PlanVersion.mobility_snapshot_id
→ Select 使用同一 snapshot
→ deterministic gate
→ ACTIVE
```

若 Snapshot 过期，必须明确返回 `STALE_RECOMPOSE_REQUIRED`，不能偷偷重新抓一个新世界再审判旧计划。需要覆盖：

- snapshot identity、TTL、capture time、provider version、provenance；
- 完整 facts / geometry / fallback / degraded 状态持久化；
- Select、Reload、Map、JourneyTwin 使用相同证据；
- 任何 authoritative feasibility 内部禁止 HTTP；
- 没有 Provider 时仍能走离线 Golden/fallback，并明确标记 degraded。

#### B. Real Multi-day Compose Engine

不要继续把用户输入顺序当答案。第一版可用 CP-SAT 联合处理：

```text
6 个真实/捕获 POI
+ 2 晚酒店
+ 3 天
+ Arrival / Departure
+ 一个已购买的 C4 reservation
+ 不同交通方式
+ TravelerTwin
+ 预算与营业时间
→ CP-SAT 决定每天去哪、顺序、开始时间、住宿和每段 mode
→ 输出真正不同的 Top-K PlanVersion candidates
```

OR-Tools 是候选生成器，不是领域权威。候选仍要经过 CityNexus deterministic feasibility、同一份 frozen mobility evidence、Opening Hours、预算、C4 和 Journey end 检查。

#### C. Live Journey Execution State

目标状态：

```text
NOT_STARTED
→ EN_ROUTE
→ ARRIVED
→ IN_PROGRESS
→ COMPLETED
```

允许分支到 `SKIPPED`。状态转换应由实际执行动作/位置/用户确认推动，而不是仅仅在 Start Journey 时把第一项改成 `ACTIVE`。所有设备和投影都读取同一个 execution truth：

```text
手机 NOW/NEXT
Leave By / ETA
Offline snapshot
Push
Guardian / PIC
JourneyTwin
Map
```

#### D. Collaborative Trip Studio

目标链路：

```text
用户拖拽 Activity
→ Draft
→ Backend Preview / Replan
→ 重新计算路线、时间、花费、步行和 C4 buffer
→ Impact Preview
→ 用户 Accept / Cancel
→ 创建新 PlanVersion
→ Frozen Evidence Gate
→ ACTIVE
```

影响预览至少要能说明类似：`+24 min`、`步行 -1.3 km`、`¥ +6`、`C4 buffer 42 → 18 min`。

### 同轮必须顺手硬化的配套项

- `MoneyEvidence` 与未知金额语义；
- MapLibre `ResizeObserver`；
- Storybook + MSW 覆盖 `READY/LIVE/DISRUPTED/RECOVERING/APPROVAL_REQUIRED/OFFLINE/COMPLETED`；
- 真正使用 `openapi-typescript` 生成的类型和 TanStack Query；
- MSW 只用于 Storybook/组件状态，正式 E2E 必须接真实 Backend；
- 记录脱敏后的 AgentRun/tool trace；
- 重新打包时排除 `__pycache__/*.pyc/.pytest_cache/.ruff_cache/*.db/*.sqlite*/node_modules/dist`，完成 fresh extraction、secret scan 和全量验证。

---

## 5. AI、DeepSeek、Hermes 和授权模型

### DeepSeek 的正确位置

历史规划希望利用 DeepSeek V4.1 Flash 的文本、视觉、Web Search、function tools 和 reasoning 能力；下一窗口必须先 probe 当前 API 能力，不要把历史宣传或旧模型名当测试结果。

适合交给 DeepSeek 的任务：

- 理解自然语言城市事件和用户偏好；
- 从票据/订单截图或模糊文本提取候选字段；
- 识别可能受影响的 Activity（输出严格结构化 hypothesis）；
- 推荐替代 Place/Activity 候选；
- 比较已经通过确定性验证的候选计划；
- 生成用户能看懂的解释；
- 在允许时使用 Web Search 找官方来源。

不能交给 DeepSeek 的权威：

- Domain Truth、硬约束、ETA、营业时间和付款事实；
- 直接写数据库、接受 Plan、改 C4 或付款/退款；
- 自己声称 `user_confirmed=true`、`hard_constraints_passed=true` 或 `c4_preserved=true`。

推荐链路：

```text
Raw / semi-structured event
→ DeepSeek semantic analysis
→ Structured Impact Hypothesis
→ CityNexus deterministic corroboration / eligibility
→ Validated Impact
→ OR-Tools candidate generation
→ deterministic feasibility
→ Gateway / Delegation Policy
→ Domain Command
```

AI 不可用时必须进入 `AI_DEGRADED` 或 `AI_OFFLINE`，不能破坏 Journey；保留 deterministic fallback。

### Hermes 的正确位置

Hermes 是 **Agent Orchestration Layer**，不是 CityNexus Domain Authority，也不应整仓揉进 FastAPI。推荐：

```text
Frontend / Backend
→ Hermes Agent Runtime
→ CityNexus MCP / Tool Gateway
→ Delegation Policy
→ Domain services
→ deterministic gate
→ authoritative DB
```

生产 profile 只暴露 CityNexus 安全工具，例如：

```text
inspect_journey
inspect_twin
inspect_commitments
refresh_weather
refresh_mobility
search_city_services
request_replan
compare_replans
replace_activity
reschedule_activity
accept_replan
```

不要给生产 Agent 开启 Hermes 的任意 terminal、文件编辑、shell、浏览器控制、SQL 或任意 HTTP 权限。Hermes model-backed E2E 在历史上曾未完成；即使 live Hermes 卡住，也不能阻塞 Native DeepSeek Runtime、MCP contract、mock/fallback 和核心产品 E2E。

### Delegated Autonomous Journey Agent

用户希望 AI 权限更大，最新方向不是把 AI 永久限制为只读，而是给它清晰的 **Autonomy Envelope**：

```text
最大自动增加预算
最大可接受损失
可自动修改的 Activity / Booking 类型
必须保护的 Commitment / C4
允许的 schedule drift
是否允许基于非结构化事件做语义判断
```

每个动作最终由服务器返回：

```text
ALLOW_AUTO
REQUIRE_CONFIRMATION
REQUIRE_STEP_UP
DENY
```

风险应综合可逆性、金额、Commitment/C4 影响、Provider 质量和用户预授权；不能只看模型自报的 confidence。高风险动作可以让 Agent 调用，但 Gateway 返回真实的 `ActionApproval`，由用户在服务器端批准、绑定 proposal/action/金额、过期并一次性消费。Agent 不能伪造审批，也不能修改自己的授权策略。

对 C4 的最新语义是“默认保护，不得未经授权破坏”，而不是机械地永远不可操作；只有用户预先授权、退款/损失/Provider 条件满足并通过更高等级 Policy/Step-up 时，才考虑 Commitment management。

---

## 6. GitHub / 外部项目采用边界

只引入能直接补当前缺口的项目，不要重新引入第二个 Agent 框架或把项目变成技术动物园。

### 高优先级

| 项目 | 用途 |
|---|---|
| `openapi-ts/openapi-typescript` | 从 FastAPI OpenAPI 生成 TS 类型，并真正用于 API client/hooks |
| `TanStack/query` | server state、cache、mutation、refetch、offline-aware data |
| `opentripplanner/OpenTripPlanner` | GTFS + OSM 的公共交通规划 |
| `MobilityData/gtfs-realtime-bindings` | GTFS-RT Trip Updates / Alerts / Vehicle Positions |
| `collective/icalendar` | 替换 Journey Inbox 的手写 ICS regex |
| `valhalla/valhalla` | 真实路线/matrix/ETA；只作为 Provider，不是裁判 |
| `open-meteo/open-meteo` | Weather facts、forecast validity 和 capture evidence |
| `maplibre/maplibre-gl-js` | 真实地图、markers、旧/新路线、事件范围 |
| `Nominatim` / `Overpass` | 地点解析和真实 POI discovery；需遵守服务使用规则 |

### 体验、离线、测试和观察性

`vite-pwa/vite-plugin-pwa`、`GoogleChrome/workbox`、`Dexie.js`、`pywebpush`、`zxing-js/browser`、`axe-core`、`lighthouse-ci`、`storybookjs/storybook`、`shadcn/ui`、`shadcn/originui`、`Vaul`、`Lucide`、`Motion Primitives`、`21st-dev/agent-elements`、`Arize Phoenix`、`Promptfoo`、`KDE/kopeninghours`、`MobilityData/gtfs-validator`。

21st.dev Codex plugin 只有在 `API_KEY_21ST` 以运行时秘密存在时才使用；它可用于搜索/获取组件，但代码许可证必须核验。React Bits 只作为视觉灵感，未确认具体许可前不要复制代码。Phoenix 放在真实 Agent trace 跑通后；Promptfoo 用于提示注入、幻觉 Activity、超预算、错误取消 Booking、C4 绕过和 stale proposal 等对抗测试。

### 当前明确不建议

没有明确理由不要引入 `LangGraph`、`CrewAI`、`AutoGen`、第二个 Solver、Kafka、Redis、Kubernetes、微服务拆分、Timefold 或 PostgreSQL-only migration。当前瓶颈是“已有能力没有在同一现实中协同工作”，不是缺框架。

---

## 7. Codex / GPT 窗口协作规则

历史实践得出的最稳工作方式：

- 原生 Codex / Luna：长时间 Goal、真实文件修改、全量测试和打包。
- 新开的 ChatGPT Web / 高推理窗口：代码审查、对抗测试、架构判断、短任务；同一项目共享文件，但不要与主写入者同时改同一文件。
- 一个时间点只允许一个主要写入者。若必须并行，使用独立 `git worktree`，不要共享同一 working tree。
- 旧 Web bridge 任务频繁断连时，优先新建同项目窗口，不要在旧窗口反复 Retry。
- 不要把 `codex-chatgpt-web` 写进 CityNexus 产品架构或运行时依赖；它只是开发工具。
- “8 小时 Goal”是工作预算，不保证平台恰好运行八小时。Goal 不能因一个子阶段完成就宣布整个产品完成；但也不能为了凑时间做无意义工作。

### 工作节奏

```text
前 15 分钟：git/status、基线、快速定位，不做长篇考古
→ 直接实现最高价值缺口
开发中：改一个功能 → 跑针对性测试 → 继续
最后约 50 分钟：全量回归、截图、secret scan、fresh extraction、最终打包
```

如果存在 Qwen Round 2 资料，只读：

```text
D:\moodle\CityNexus-QwenAssist\V11-R2\QWEN_HANDOFF_TO_CODEX_R2.md
```

最多吸收 10 分钟；文件不存在或 Qwen 未完成时，直接继续 V12，不要等待侧翼工程师。

---

## 8. 交给下一个 GPT 的执行顺序

1. 检查路径和当前 writer：

   ```powershell
   Get-Location
   git status --short
   git diff --stat
   git log --oneline -n 10
   ```

2. 阅读当前仓库的真实 README、progress、contracts 和最新报告；确认是否已有 V12 代码，避免重复实现。
3. 先针对 Frozen Evidence Select Gate 写/运行 focused tests；不要先盲目套历史 patch，不要 `reset --hard`，不要覆盖另一个窗口的改动。
4. 修复并验证：
   - `PlanVersion.mobility_snapshot_id` 与完整 evidence persistence；
   - Compose/Select/Reload/Map/JourneyTwin 同一 snapshot；
   - stale snapshot 的显式语义；
   - UNKNOWN MoneyEvidence；
   - execution state machine + ExecutionClock；
   - DnD Preview/Replan/Impact/Accept；
   - MapLibre resize。
5. 再推进真实 multi-day CP-SAT Compose；输入、输出、solver provenance 必须可序列化，候选仍由 deterministic gate 最终裁决。
6. 将 DeepSeek/Hermes 接入真实产品链，保留 Native/fallback；所有 Agent mutation 必须经过 Gateway、Policy、approval/幂等和审计。
7. 跑相应 backend、frontend、Playwright、OpenAPI、Ruff、compileall 和 offline Golden 回归。
8. 生成脱敏进度报告，清理 checkpoint，fresh-extract 后再跑一次。报告必须区分：

   ```text
   IMPLEMENTED
   PARTIAL
   SIMULATED
   PLANNED
   SKIPPED_EXTERNAL_DEPENDENCY
   E2E_VERIFIED
   ```

---

## 9. V12 旗舰验收场景

最终不是看新增了多少测试，而是尽量跑通这一条：

```text
导入真实/捕获的 Reservation 或票据
→ 创建 3 天 2 晚 Journey
→ 加入 6 个 POI、酒店、Arrival、Departure
→ 冻结 Provider facts
→ CP-SAT 联合决定每天安排、顺序、时间、住宿和交通方式
→ 生成真正不同的 Top-K
→ Select 使用 Compose 的同一 snapshot
→ Start Journey
→ NOT_STARTED / EN_ROUTE / ARRIVED / IN_PROGRESS / COMPLETED 推进
→ 手机 NOW/NEXT、Offline、PIC、Map、JourneyTwin 同步
→ 用户拖动一个未来 Activity
→ Backend Preview/Replan 给出时间、费用、步行和 C4 影响
→ 用户 Accept
→ 新 PlanVersion ACTIVE，旧版本 SUPERSEDED
→ 城市/天气/交通突发变化
→ DeepSeek/Hermes 在授权包络内分析并选择恢复方案
→ OR-Tools 重新排程
→ Policy / deterministic gate / approval / audit
→ Agent 自动恢复或请求确认
→ Map、JourneyTwin、Mobile、Offline、PIC、Control Tower 看到同一个新现实
```

只有这条链真正成立，才可以把 CityNexus 称为“能创建、修改、执行和恢复真实旅行的 Journey Agent”。

---

## 10. 可直接发给下一个 Codex 窗口的英文启动指令

```text
Read CITYNEXUS_HANDOFF_FOR_NEXT_GPT.md and work against the current CityNexus repository at D:\moodle\CityNexus.

Treat the handoff as historical context, not as proof that the current worktree matches it. Start with a concise repository baseline: git status, diff summary, recent commits, current test/build status, and the actual implementation state of the V12 gaps. Cap the initial audit at 15 minutes, then implement the highest-value verified gap.

This is an implementation task, not a documentation-only review. Preserve existing user changes and do not reset, overwrite, or blindly apply historical patches. There must be one primary writer for the shared worktree. Use targeted tests after each meaningful change, then run the full regression, frontend build/E2E, OpenAPI parity, Ruff, compileall, secret scan, and fresh-extract package verification before claiming completion.

The current product goal is CityNexus V12: Authoritative Trip Composition & Live Journey Execution. The highest priorities are:

1. Persisted Provider Evidence so Compose, Select, Reload, Map, JourneyTwin, and deterministic feasibility use the same MobilitySnapshot; stale evidence must require explicit recomposition.
2. Real multi-day composition with POIs, hotel, arrival/departure, existing commitments, travel modes, budget, opening hours, and CP-SAT-generated distinct Top-K candidates.
3. A real execution state machine driven by one ExecutionClock: NOT_STARTED, EN_ROUTE, ARRIVED, IN_PROGRESS, COMPLETED, and SKIPPED.
4. Collaborative Trip Studio editing: drag → backend preview/replan → impact summary → accept/cancel → new PlanVersion through the frozen-evidence gate.
5. MoneyEvidence semantics where UNKNOWN is null/unknown, never zero by coercion.
6. MapLibre resize correctness, truthful OpenAPI client usage, Storybook/MSW state coverage, and backend-connected Playwright evidence.

Keep the authority model intact: DeepSeek/Hermes provide semantic reasoning and orchestration; Providers provide facts; OR-Tools generates candidates; CityNexus deterministic logic validates operational truth; Gateway/Delegation Policy decides whether an action may execute. Never let an agent fabricate approval, provider truth, hard-constraint results, C4 preservation, or user confirmation. Never put API keys in source, logs, tests, Markdown, Git, or checkpoints; read them only from runtime environment variables.

The completion gate is one authoritative journey that can be composed, selected, edited, executed, autonomously recovered, and observed consistently across PlanVersion, JourneyTwin, Map, Mobile, Offline, Control Tower, and PIC. Do not stop merely because one phase or a library integration is complete, and do not claim PASS for a simulated or partial capability.
```

---

## 11. 一句话交接结论

CityNexus 已经走过“基础设施堆叠期”，现在最有价值的不是再增加框架，而是把 **同一份 Provider 事实、真正的多日规划、真实执行状态、可解释的拖拽重排和受授权的 Agent 恢复** 连接成一条可 fresh-extract、可回归、可演示的产品闭环。

---

## 12. 2026-09-15 新增交接：`moodle - 分析项目现状`

### 12.1 读取说明

本节是对用户引用的 ChatGPT 会话 `6aa59db8-0f88-83ea-8512-ddbead00eca6` 的续写位置。
当前环境无法通过 Codex `read_thread` 直接读取这个 ChatGPT/GPT 页面 ID，浏览器标签页也返回了 403/运行时路径错误。因此，本节不把无法核验的会话原话冒充成事实，而是结合该会话引用、当前主工作树、V18.3 报告、V19 包和 V19.1 EAC 参考材料，整理截至 2026-09-15 能确认的项目状态。

下一个窗口如果能正常打开原会话，应继续核对原文；但下面的版本、证据和待办均以仓库中的最新材料为准。

### 12.2 当前版本已经从 V12 推进到 V18.3 / V19

旧交接里把 V12 作为下一阶段目标。当前真实主工作树已经继续推进：

```text
V18.3 Hermes + Experience Convergence
↓
V19 Traveler Capability + Accessibility Intelligence
↓
V19.1 Capability Correctness + EAC Convergence（参考/待选择性移植）
```

权威工作区仍是：

```text
D:\moodle\CityNexus
```

当前主树的 `CURRENT_STATUS.md` 明确标记为：

```text
IMPLEMENTED / native Hermes proven / convergence gates green
```

这不表示所有产品能力都完成，而是表示 V18.3 这一轮收敛目标已完成；能力规划、生产身份、实时 provider 等边界仍要按下文单独判断。

### 12.3 V18.3 已确认完成的事情

V18.3 不是重新设计项目，而是把 V18.2 的 Hermes、Copilot、事件流和体验证据收敛到一个诚实的发布快照。

已确认：

- 原生 Hermes 通过 CityNexus 后端代理运行，使用官方 `citynexus` profile 和 CityNexus MCP V2；
- Hermes 版本为 `0.21.2`，模型配置为 DeepSeek `deepseek-v4-flash`；
- MCP 工具表面固定为 11 个 allowlisted tools；
- Gateway / Guardian 仍然掌握事实、提案、审批和 mutation 权限；
- 未发生真实原生运行时事件前，产品显示 `DIRECT`，不能仅因页面存在时间线就显示 Hermes；
- 未配置时能力接口也返回稳定的 `ready: false`，前端不再猜测 Hermes 是否可用；
- V18.3 的原生证明运行实际执行了 `inspect_journey`、`inspect_twin`、`search_city_services`、`request_replan` 等工具事件；
- SSE 事件有 ID、序列和去重/排序规则，断线最多有限重试，并明确显示 stale/unavailable；
- proposal-created 与 approval-required 保持不同，提案不会自动变成已批准；
- 移动端使用紧凑的当前任务视图，完整真实历史可展开；
- MapLibre 改为地图表面按需加载，非地图入口不再静态加载地图包；
- Vite 生成了独立的 MapLibre/JourneyMap chunk；
- SQLite、WAL/SHM、缓存、日志和密钥不进入发布包。

V18.3 证据位置：

```text
D:\moodle\CityNexus\reports\product-v18-3\
D:\moodle\CityNexus\HERMES_INTEGRATION_STATUS.md
D:\moodle\CityNexus\CURRENT_STATUS.md
```

### 12.4 V18.3 的验证结果和诚实边界

报告记录的验证结果：

- V18.3/V18.2 聚焦测试：9 项通过；
- V18.1 原生契约测试通过；
- 后端宽回归：429 passed、2 skipped、2 warnings；
- 前端生产构建通过；
- 桌面原生 Hermes Playwright 流程通过；
- 移动端 390x844、430x932 通过，320x720 溢出检查通过；
- OpenAPI parity 通过；
- fresh-extract / package gate 通过。

必须保留的边界：

- 两次有界 DeepSeek Responses 检查超时，不能写成 DeepSeek 每次都可用；
- Hermes 的原生证明是真实运行证明，不代表所有会话都能运行；
- 生产部署还需要外部 freeze/review 以及真实 WebAuthn/identity 集成；
- Live Valhalla 没有配置 URL，因此实时 Valhalla smoke 是跳过，不是通过；
- Traveler Capability 在 V18.3 仍被明确留作下一块 domain-wired 能力，不能用 localStorage-only 面板冒充产品权威。

### 12.5 V19 新增产品方向：把旅行者的身体和照护需求真正纳入行程

V19 的产品重点不是增加一个医疗表单，而是让用户用大白话说出：

- 我妈膝盖不好，不能走太多路；
- 必须全程无障碍，不能走楼梯；
- 孩子中午需要午睡；
- 带婴儿车和大件行李；
- 希望环境安静、少刺激、节奏慢一点。

系统要把这些话变成真实的旅行约束，并影响规划、重排、解释和风险提示。

V19 将能力分成六类：

1. `HARD_ACCESSIBILITY_NEED`：如必须无障碍、不能走楼梯；
2. `CARE_REQUIREMENT`：如午睡、休息、如厕频率；
3. `PHYSICAL_LIMIT`：如每段最多步行距离、连续步行时长、每日步行量；
4. `TRIP_CONTEXT`：如婴儿车、大件行李；
5. `SOFT_PREFERENCE`：如偏好安静、室内、慢节奏；
6. `PROTECTED_COMMITMENT`：继续由原有 C3/C4 机制保护。

核心权责不变：

```text
DeepSeek：自然语言 → 能力意图
CityNexus：校验、规范化、确认和持久化
Planner/Replanner：执行硬约束、计算软偏好
Provider/Evidence：回答地点和路线到底有没有被证实
Hermes：查看能力、编排工具，但不能编造无障碍事实
Gateway/Guardian：控制授权、审批和 mutation
```

V19 的关键原则是：硬需求不能悄悄降级成软偏好；从行为中学到的只能形成软偏好，不能凭行为推断硬无障碍需求。

### 12.6 V19 能力词汇和确认规则

主要能力代码包括：

```text
STEP_FREE_REQUIRED
AVOID_STAIRS
MAX_WALKING_PER_LEG_M
MAX_CONTINUOUS_WALKING_MIN
MAX_DAILY_WALKING_M
SLOW_PACE
MIDDAY_REST_WINDOW
REST_EVERY_MIN
INFANT_NAP_WINDOW
TOILET_BREAK_EVERY_MIN
STROLLER
LARGE_LUGGAGE
QUIET_ENVIRONMENT
INDOOR_PREFERRED
SENSORY_LOW_STIMULATION
```

严重程度为：

```text
HARD / STRONG / SOFT
```

确认规则：

- `HARD` 无障碍需求必须由用户明确输入或明确确认；
- `STRONG` 可以影响排名，但必须能解释为何被覆盖；
- `SOFT` 只能影响排序和解释；
- 文本提取只能产生 `UI_CANDIDATE_ONLY` 候选，不得直接保存；
- “我不需要轮椅，我能走路”不能生成硬性无障碍需求；
- “朋友说我可能需要轮椅，但我不这么认为”不能生成硬性无障碍需求；
- “我以前不用轮椅，但现在必须无障碍”必须保留当前的正向硬需求；
- 否定、传闻、历史描述必须按所在语句处理，不能用整条消息的粗糙关键词判断。

确认 API 的目标语义也已明确：

```text
PUT /capabilities
= 替换完整目标集合

POST /capabilities/confirm
= 只确认并 upsert 本次提交的项目

deactivate/remove
= 独立、明确、可审计的动作
```

连续确认 A，再确认 B，A 和 B 都必须继续 active，不能因第二次确认而静默删除 A。

### 12.7 V19.1 EAC 提供的有效成果

EAC 是独立实验室，不是主树本身。它基于：

```text
snapshot/main-tree-20260915T1220
```

主树当时保持只读，所有修改在隔离 lab/runtime 中完成。可复用的成果包括：

- 隔离 backend `127.0.0.1:8052` 和 frontend `127.0.0.1:4202`；
- 33 项聚焦后端测试通过；
- 7/7 Playwright 通过；
- axe 0 violations；
- 8 个旅行者 shadow flows；
- `LIVE_SHADOW`、`RECORDED_FIXTURE`、`OFFLINE_STALE` 三种明确数据来源；
- OSM 形状的无障碍证据规范化；
- place/journey accessibility evidence API；
- capability plan impact API；
- capability audit 和 capability catalog；
- bounded text extraction 候选接口的产品思路；
- PWA、性能、键盘、缩放、移动触控目标等验证材料。

EAC 的硬事实是：

```text
UNKNOWN != ACCESSIBLE
```

没有权威证据时，必须返回 `NEEDS_LIVE_EVIDENCE` 或 `ACCESSIBILITY_UNVERIFIED`，不能因为用户需要无障碍就自动把地点标成无障碍。

### 12.8 EAC 不能直接整包合并的原因

EAC 不是最终主树，不能盲目 `git apply`：

- EAC 使用较早的 `main.py`，与 Final V19 的上下文已经不同；
- 部分 patch 对 Final V19 的 `main.py` 直接 apply 失败；
- EAC 的本地 fallback 仍会把否定/传闻文本误识别成硬需求；
- 通用 accessibility 汇总把 `toilets:wheelchair=yes` 误当成整个地点无障碍；
- Mapping 与 list/tuple 形式的 OSM tags 需要统一规范化；
- 当前真实路线级无障碍证据仍然不存在，不能从地点标签推导路线无障碍；
- shadow app 的 recovery view 是从当前 plan-impact 推导的，不是真正的 before/after recovery snapshot；
- EAC 的性能/PWA patch 属于参考 shadow app，不能再造第二套 service worker。

正确做法是：以 Final V19 主树为权威，逐项人工审查、语义移植、针对性测试。

### 12.9 无障碍证据的正确语义

证据必须按“需求”和“对象”匹配，不能用一个宽泛的总状态满足所有需求。

正确示例：

| Provider 事实 | 可支持的结论 | 不能推出的结论 |
|---|---|---|
| `wheelchair=yes` | 某地点范围内的轮椅证据 | 整条路线无楼梯 |
| `entrance:wheelchair=yes` | 某入口的轮椅证据 | 所有入口和路线都无障碍 |
| `toilets:wheelchair=yes` | 无障碍卫生间证据 | 地点入口无障碍、路线无楼梯 |
| `wheelchair=no` | 地点存在冲突证据 | 可以降级为普通偏好 |
| `highway=steps` / `steps=yes` | 存在楼梯冲突 | 其他路径一定不可行 |
| `ramp=yes` / `elevator=yes` | 部分辅助证据 | 完整 step-free route 已验证 |
| 缺少相关标签 | `NEEDS_LIVE_EVIDENCE` | 默认 accessible |

如果有正向标签同时有明确楼梯冲突，冲突优先。每条证据要保存来源、原始 key/value、对象范围、抓取时间、置信度和 provenance。

### 12.10 当前 API / 合同需要重点检查的地方

EAC 记录的隔离运行时有 134 个 path，而快照中的 checked-in `contracts/openapi.yaml` 只有 124 个 path，并且：

- checked-in spec 缺少 capability/accessibility evidence routes；
- checked-in spec 的路径缺少 `/api/v1` 前缀；
- 运行时存在的 extraction/audit/catalog 等接口没有完整同步到 checked-in spec。

因此下一轮应从实际运行 FastAPI 生成或校正 OpenAPI，再重新生成前端类型，不能继续让运行时合同和静态合同漂移。

### 12.11 下一轮优先级

按当前证据，下一轮不是 V20，也不是重新搭 Hermes，而是完成 V19.1 的选择性合并：

1. 修复硬无障碍需求不得降级、重复 code 合并、常见步行数字解析；
2. 修复确认接口的 upsert 语义、并发和幂等测试；
3. 修复 `REST_EVERY_MIN` / `TOILET_BREAK_EVERY_MIN` 的数学含义：interval 是连续活动/行程跨度上限，休息时长是独立参数；
4. 修复 Traveler scope 的明确确认；
5. 采用保守的 DeepSeek-first 候选提取，fallback 宁可返回 UNKNOWN/需要澄清，也不能制造假的 HARD；
6. 移植按需求/对象区分的 OSM evidence evaluator；
7. 增加 place/journey evidence、audit、catalog，但保持 descriptive/non-authoritative；
8. 将能力确认、TravelerTwin、plan impact、evidence state 接入真实产品 UI；
9. 若没有真正的 before/after recovery API，就把页面称为 current capability impact，不称为 recovery diff；
10. 校正 `/api/v1`、capability、accessibility evidence、extract/audit/catalog 的 OpenAPI 合同；
11. 完成前端 typecheck/build、桌面和移动流程、V18.3 回归、fresh-extract 和 clean package。

### 12.12 不能丢失的验证清单

```text
否定文本不生成 HARD
传闻文本不生成 HARD
历史负面 + 当前正面保留当前正面
重复 code 合并且 strongest severity wins
confirm A + confirm B => A、B 都 active
REST/TOILET interval 数学正确
toilets:wheelchair=yes 不等于地点 step-free
wheelchair=yes 不等于路线 step-free
list/tuple OSM tags 不丢失
未知证据显示 NEEDS_LIVE_EVIDENCE
LIVE_SHADOW 断线不换成 fixture
RECORDED_FIXTURE 明确标注 fixture
OFFLINE_STALE 显示 staleAt
DeepSeek/Hermes 不伪造 provider truth
Agent mutation 经过 Gateway/Guardian/Policy/approval/audit
V18.3 native Hermes 证据仍保持绿色
```

## 13. 给下一个 GPT / Codex 的最新启动指令

```text
Read CITYNEXUS_HANDOFF_FOR_NEXT_GPT.md and continue from the authoritative repository at D:\moodle\CityNexus.

The current baseline is V18.3 Hermes + Experience Convergence. Final V19 is the authority for Traveler Capability and Accessibility. The V19.1 EAC lab is reference material from an earlier moving snapshot, not a package to apply blindly.

Do not start V20, do not rebuild Hermes, and do not create another capability framework. Inspect the current worktree first, then selectively port the verified V19.1 ideas.

Highest priorities:
1. HARD accessibility severity invariants and semantic safety for negated, rumoured, disputed, and historical language.
2. Duplicate capability canonicalization and common numeric walking/rest parsing.
3. Confirm API upsert semantics, explicit deactivate/remove, concurrency and idempotency.
4. Correct REST_EVERY_MIN and TOILET_BREAK_EVERY_MIN interval semantics.
5. Requirement-specific accessibility evidence; UNKNOWN is not ACCESSIBLE; route-level step-free remains NEEDS_LIVE_EVIDENCE without real evidence.
6. DeepSeek-first bounded candidate extraction with conservative fallback and UI confirmation only.
7. Audit/catalog endpoints and real product capability UX, without localStorage or fixture authority.
8. Reconcile runtime OpenAPI with checked-in contracts and /api/v1 prefixes.

Preserve the authority model: Providers provide facts, DeepSeek interprets language, OR-Tools proposes plans, deterministic CityNexus logic validates feasibility, and Gateway/Guardian controls authorization, approvals, commitments, and mutations. Never fabricate accessibility evidence, approval, booking, payment, hard-constraint success, or user confirmation.

Run focused tests after each meaningful change. At convergence run the capability tests, accessibility evidence tests, confirm/idempotency tests, OpenAPI parity, frontend typecheck/build, desktop/mobile Playwright, V18.3 regression, secret scan, clean package, and fresh-extract verification. Report IMPLEMENTED, PARTIAL, SIMULATED, PLANNED, SKIPPED_EXTERNAL_DEPENDENCY, and E2E_VERIFIED separately.
```

## 14. 最新一句话结论

CityNexus 已经证明了原生 Hermes、代理式 MCP、实时事件时间线和旅程安全边界；当前真正的产品升级点，是把“这个旅行者到底能不能这样走、需不需要休息、地点和路线是否真的无障碍”变成有证据、有确认、有约束、有解释的行程能力，并且让它在规划、执行、恢复和移动端体验中使用同一份真实状态。
