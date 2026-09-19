# CityNexus — 前端 A/B 整合 + 真种子 + 视觉验收（Qoder 集成线，2026-09-19）

按裁决顺序执行：`authoritative baseline` → `v6 truth integration` → `以 truth-integrated commit 建
frontend/apple-pass1-visual-integration` → `A/B 人工 reconcile` → `真种子 + 可读截图`。
全部在 `D:\moodle\_qoder_integration_20260919`（主仓的 git clone），**主仓工作树与 HEAD 未被改动**，
运行中的 `:8000` / `:8011` 后端未被打断。

## 1. 提交链（可复核）

| commit | 内容 |
|---|---|
| `380e6ff` | `chore(baseline)`：把主仓现状冻结为权威基线（6542 文件；`backend/app`、`backend/tests`、`data`、`frontend/src`、`frontend/e2e`、docs、contracts、evals）。主仓此前只有 5 个 9/5 的文档提交，**全部源码 untracked**。用 `commit-tree` 建立，不移动 HEAD、不改文件。 |
| `b12f24f` | `feat(truth)`：v6 truth hardening 落地。 |
| `e330ac2` | `feat(frontend)` A 组：Apple 视觉 / IA。 |
| `a2124c0` | `fix(frontend)` B 组：前置类型 / 行为修复。 |
| `cfb2b4a` | `test(frontend)`：真种子 setup project + 双主题对比度门，以及它暴露的浅色 AA 缺陷。 |

## 2. 基线冻结的可复现性

- 树 `2d01138d…`，6542 个文件，62.9 MB；`*.zip` / `node_modules` / `dist` / `.venv` / `*.db` /
  `storybook-static` / `_*/` 暂存目录被排除，只留源码、种子与证据报告。
- 主仓部分源码是 CRLF，副本是 LF；比较一律按 EOL 归一后进行，commit message 里写明。
- 主仓 `backend/app`、`frontend/src` 自隔离副本建立（9/18 15:02）后**无任何源码漂移**（0 个更新文件），
  所以副本与主仓可互换作参照。

## 3. v6 truth integration：主仓基线上复跑

先做等价性核验：隔离副本基线 `c6f9024` 的 40 个非文档源码文件与主仓磁盘内容 **0 处不一致**
（EOL 归一后），因此整合不是"重新推导"，而是逐 blob 搬运 GPT 已验收的状态。

同一环境（清 `DEEPSEEK_API_KEY` / `CITYNEXUS_AI_API_KEY`，`CITYNEXUS_AI_ENABLED=false`，
`CITYNEXUS_DATABASE_URL` 指向独立文件）：

| 树 | 结果 |
|---|---|
| `380e6ff` 基线 | 762 passed / 15 skipped / **0 failed**（49.4s） |
| `b12f24f` +v6 | 827 passed / 15 skipped / **0 failed**（50.9s） |

NEW-vs-baseline = ∅，且新增 65 条 truth 测试全绿。注意：这比隔离副本记录的
`2 failed(aiv3_02, v18_3)` 更好——那两条只在 AI key 存在时失败（副本的 blocker 4 正是为此而设）。

## 4. A/B reconcile（裁决要求的拆分）

`iso/master..qoder-frontend` 的 20 个文件按裁决拆成 A(9) + B(11)，两块都能 3-way 干净落到
truth-integrated 树上，**没有降级任何主线代码**：

- A：`design-tokens.css`、`V8Experience.tsx`、`LiveRecovery.tsx`、4 个 `qoder-*` 门 + 2 个共享 helper。
  `V8Experience.tsx` / `LiveRecovery.tsx` 是 truth 线与 Apple 线都碰过的文件，用 3-way（base = 副本
  `master`）合并，两条线的改动同时保留。
- B：`main.tsx`、`v10Execution.ts`、`v8Types.ts`、`MapPanel.tsx`、`AgentComposer.tsx`、
  `PlanComparison.tsx`、`PushCapabilityCard.tsx`、`SortableActivityList.tsx`、V12 story、
  `package.json`、`tsconfig.typecheck.json`。
  逐项核对当前版本：`v8Types.ts` 在本仓是 CRLF，直接取 Apple 分支的 LF 副本会让 diff 变成
  46 行重写（并可能悄悄覆盖主线），因此改为**就地插入两个字段**，净 diff 只有 2 行。
  B 组净效果：11 文件 +35 / −17。

整合树门禁：`typecheck:all` 0 错、`vite build` 通过、28 条 `qoder-*` 门全绿。

## 5. 真种子环境（裁决要求的第 0 步）

新增 `frontend/e2e/_qoderRealSeed.setup.ts`（Playwright setup project，跑在 config 自己起的
webServer 之后；`globalSetup` 不行，那时端口还没监听）。它只走产品公开面：

```
POST /api/v1/demo/reset
POST /inbox/import + /inbox/{id}/confirm  ×3（ARRIVAL / MID_TRIP / DEPARTURE）
/v8/discover → 真实城市发现（sealed replay）→ SELECTED plan version
localStorage["citynexus.v8.journey_id"] → 持久化成 storageState 供全部用例复用
```

无 SQL 写入、无 `route.fulfill` 假路由。日志会打印 `selectedPlan=PLAN VERSION SELECTED v1 · <uuid>`。

端口改为 env 可覆盖（`CITYNEXUS_E2E_PORT` / `CITYNEXUS_BACKEND_PORT`），默认值不变，
这样集成环境不必占用主仓的 `:8000`。

### 15 条 legacy 的重新分类（这次是在真种子上跑出来的）

| 类别 | 数量 | 证据 |
|---|---|---|
| **旧 `/` Journey Mode 界面已被 V8 shell 取代** | 8 | `golden`、`live-autopilot-v5`、`predictive-real-city-v6`、`product-hardening`×5。全部死在同一处：`getByTestId('journey-status')` 不存在。axe 的页面快照显示访问 `/` 渲染的是 V8 shell（Today / Live Journey / Map / Trip Studio 导航）。这是**规格过期**，不是缺种子、也不是 A/B 回归。 |
| **V8 界面文案 / DOM 漂移** | 4 | `product-v8`×2（期望 heading `Your next city, already considered.`、导航按钮 `AI`）、`v10-live-execution`（期望 `read-only ready`）、`real-world-trip-operations-v9`（`locator.fill` 超时）。 |
| **真种子后恢复通过** | 3 | `v10-inbox`、`v10-quality-budget`、`v13-5-fully-grounded` 等——此前只因缺种子失败。 |

对照实验（同一份种子，10 个 spec 文件）：

| 树 | legacy 结果 |
|---|---|
| `b12f24f` truth-only（无 A/B） | 12 failed / 3 passed |
| `a2124c0` +A+B | 13 failed / 2 passed |

差的那 1 条是 `v10-accessibility`：**Apple 线造成的真实回归**（见下）。除此之外 A/B 零新增失败。
全量套件：无种子 30 passed / 15 failed → 有种子 **34 passed / 12 failed**。

## 6. 视觉阶段抓到的两个真缺陷

### 6.1 axe 的 AA 失败 = Apple 线引入（已修）

`v10-accessibility` 在整合后失败，axe 给出精确数据：

```
color-contrast  serious  fg #0a66ff  bg #f5f5f7  4.42:1  (10px bold uppercase)
expected 4.5:1   <p class="v8-kicker">Live Journey · saved 19 Sept, 13:43</p>
```

根因：Apple 调色板把 `--v8-indigo` 从 `#4658d9`（5.74:1）重绑为 `--cn-accent #0a66ff`。
作为链接色没问题，作为 10px 文本就跌破 AA。**深色门抓不到它，因为门只 emulate 了 dark。**

把门改成双主题后，浅色主题一次性暴露 15–48 条/屏（扫描器还先把"未 token 化的近白面"在浅色下
误判成违规——那一层按定义只属于深色，已在 `_qoderContrastScan.ts` 里按 scheme 关闭）。
逐条修完后 dark 0 / light 0：

| 缺陷 | 处理 |
|---|---|
| `.v8-kicker` 4.42:1（Apple 重绑引入） | 新增 `--cn-accent-text #0a5cd6`（画布 5.49 / 白 5.97） |
| `.cn-hero-label` 3.33:1（Apple 新类用了 tertiary 墨色） | 改 `--cn-ink-secondary`（4.66） |
| "All clear" 4.04:1（Apple 的 attention clear 态） | 新增 `--cn-success-text`（light `#17672f` / dark `#30d158`） |
| outline 按钮边框 1.2:1（既有硬编码 `#d9ddea`，dark 侧早已修、light 侧漏了） | 浅色 `--cn-control-border` 提到 `#7d8797`（3.63 / 3.33） |
| 侧栏 tagline / nav group / nav button / breadcrumb `/` / sync 副文本 / mode chip 边框 | 统一取 token，2.4–3.9:1 → AA |

### 6.2 截图才能看见的问题（未擅自修，交裁决）

`reports/visual-integration/` 有 32 张可读 PNG（Today + Live × 360/412/430/desktop × light/dark，
各含首屏与整页）。全部 0 横向溢出。肉眼审查结论：

1. **Today 的语言切换渲染了两次**：顶栏一个小 `EN`，hero 下方一个**全宽超大** `EN`
   （DOM 里就是 `topbar-language` 与 `home-language` 两个 testid）。第二个在首屏抢焦点。
2. **Today hero 在真实数据下 CTA 泛滥**：`试用其他城市` / `AI 帮我规划` / `打开行程工作台` /
   `查看实时行程` 四个按钮 + 两个语言键。`qoder-today-hero` 的"≤1 primary CTA"门只在**空/预旅行分支**
   触发，正是裁决当初点名的"positive branch 需真种子才能验证"——现在验证了，**不成立**。
3. **Live 首屏被两个 secondary 动作占住**：`更新位置`、`报告降雨` 以全宽同权重压在
   `现在 Old Town Gate` 之上，Current 不再是第一眼。
4. **地图诚实空态过高**：约 400px 的"尚未获取地图位置"块把"当前没有需要你决定的调整"推到折叠线下。
5. **Copilot dock 与底部内容重叠**：`下一段路程方式` 面板只露出一行就被 dock 压住，文字被裁。
6. **头像文字溢出**：右上角蓝色 avatar 里的 `DE` 压在圆外（light 图里是 `D` 被裁）。
7. **文案粘连 / 未本地化**：`每人每天约 ¥500这是按你的预算平均下来的参考值`（缺分隔）；
   `下一步 · Riverside Museum · transit · 时长待定`（`transit` 未译）。

这些属于产品 IA / DOM 决策（哪个语言键该留、哪个 CTA 是 primary），不在"reconcile 不降级"的授权内，
因此只记录不动手。

### 6.3 Live 关键状态截图（`reports/visual-integration/states/`）

L0–L4 只有 `qoder-live-structure.spec.ts` 的 route fixture 能构造（真种子 journey 没有开着的
disruption），所以给该 spec 加了一个默认关闭的 `QODER_CAPTURE_STATES=1` 截图出口
（断言未改，捕获后把配色恢复成进入前的主题）。产出 L1/L2/L3 × light/dark。

`L2-proposal-ready-light.png` 是这批里最要紧的一张：**"方案 A · 推荐怎么改" 提案卡被 Copilot dock
压在下面，只露出标题，Accept CTA 不在首屏**。也就是说第 (e) 项不是"边缘文字被裁"的装饰问题，
而是**决策态下主操作被遮挡**；配合第 (d) 项（地图空态约 400px），真正需要用户点的那一下
被推到了折叠线以下。这条门的断言（Accept 唯一、disruption 进入首屏）仍然通过，
因为它量的是 bounding rect 与"Copilot 不与 Accept 相交"，而截图显示的是**视觉层叠与首屏优先级**——
两者不是一回事，这正是肉眼阶段存在的理由。

补看 L1 与 dark 两张后，可以把结论收紧成三条跨状态、跨主题的规律：

1. **Copilot dock 遮挡内容态是常态，不是 L2 偶发**：L1 里"选择下段交通"被裁掉半行，
   L2 里提案卡只剩标题，light / dark 一致。
2. **头像文字溢出跨主题**：light 显示成被裁的 `D`，dark 显示成压在圆外的 `XI`——
   是 avatar 尺寸与内容宽度的固定冲突，不是配色问题。
3. **地图诚实空态在两主题下都是首屏最大的一块**（light 是浅灰绿、dark 是纯黑空洞），
   它把"现在/接下来/需要你决定"三件事整体下移；dark 侧的观感问题不是发灰发亮，而是**空**。

这三条都不需要改真值逻辑，属于布局与层叠决策，因此仍归"待裁决"，不擅自动手。

## 7. 请给的裁决

- A/B 整合是否接受（`FRONTEND_APPLE_PASS1_INTEGRATED_ON_TRUTH_BASELINE`？）；
- 6.1 的浅色 AA 修复与双主题门是否作为这条线的正式延续收下；
- 6.2 的 7 项视觉缺陷：哪些进入 Apple 线下一轮，哪些归主线（语言键重复、Copilot 遮挡、头像溢出
  看起来是主线既有 DOM）；
- 那 8 条 `/` 旧界面 legacy：迁移到 V8 shell 断言，还是标记为过期归档。

## 8. "A 能不能单独并"——实测答案：不能

裁决建议 A 优先保留、B 逐项 reconcile，隐含"A 至少可以先走"。用三个 worktree 在**同一份
`tsconfig.check.json`** 下实测：

| 树 | 类型错误数 |
|---|---|
| `b12f24f` truth-only 基线 | **17** |
| 基线 + 只并 A（`e330ac2` 的内容） | **14** |
| 基线 + A + B（`a2124c0`） | **0** |

读法：

- A 自己**不新增**任何类型错误，还顺带清掉 3 个（`V8Experience.tsx` / `LiveRecovery.tsx` 的改动本身是类型安全的）；
- 但 A 单独并进来仍然编不过，**B 是 A 的前置**，不是可选项；
- 更关键：B 里 `v8Types.ts` 新增的 `acknowledged` / `no_alternative` 两个字段，报错方是
  **truth 线自己的组件** `src/features/recovery/RecoveryRequiredPanel.tsx:45-46`。
  也就是说这两个字段属于主线编译前置，而不是 Apple 线的私货——逐项 reconcile B 时它们必须进，
  否则 authoritative 分支自己就红。

`vite build` 在 A-only 下能过（vite 不做类型检查），所以"能 build"不能作为 A 可独立合并的证据。

## 9. 那 8 条 `/` legacy：不是过期不可修，实测只差一行入口

旧界面没有被删除，它被**显式挪到 `/legacy`**（`src/main.tsx` 的 `App()`：默认入口渲染
`V8Experience`，`path.startsWith("/legacy")` 才渲染 `LegacyApp`，注释写明"legacy 仅供内部/向后兼容访问"）。

探针实验（临时把 `golden.spec.ts` 的 `page.goto("/")` 改成 `/legacy`，跑完已还原，未提交）：

| 断言 | 改前 | 改后 |
|---|---|---|
| `journey-status` 存在 | element(s) not found | 元素存在，`data-source="backend"` 已满足 |
| 状态文本 | — | 实际 `PLANNED · backend truth`，spec 期望 `ACTIVE` |

所以这 8 条的成本是：每条 1 行入口路径 + 把状态期望对齐当前后端真值（journey 在被选中 plan 之后是
`PLANNED`，不再是 `ACTIVE`）。**期望值不该为了变绿而改**，因此这里只交结论，不交改动——
需要 owner/裁决确认"PLANNED 是否就是今天该断言的真值"。

（同一探针还顺带说明：真种子 harness 与 legacy 界面是兼容的，`data-journey-id` 正是种子建出来的
`22222222-…` journey。）

## 10. pass-8 裁决后的收口（证据卫生三项）

裁决接受 `FRONTEND_APPLE_PASS1_AB_RECONCILED_ON_TRUTH_V6_BASELINE` 与
`INTEGRATION_TRUTH_GATES_PASS`，并把视觉阶段记为
`FRONTEND_APPLE_PASS1_VISUAL_INTEGRATION_BLOCKED`。他点的三个证据卫生问题都补了：

1. **门改名**：`qoder-dark-audit.spec.ts` → `qoder-contrast-audit.spec.ts`，describe/test 标题、
   报告目录 `reports/contrast-audit/`、文件名 `contrast-audit-*.json` 全部跟上；
   `summarise()` 里那个把 light 行打成 `(dark)` 的标签删了。
   顺手把 focus-ring 那半条门也真的从"只量 dark"改成 dark+light 都走——
   名字改成两主题而实现仍只测 dark，就是他批评的那种"标签撒小谎"。
   **这一改立刻抓到 4 条 light 违规**：`.v8-product-shell button:focus-visible` 的
   `outline: 3px solid #9aa8ff` 在 #f5f5f7 上只有 2.05–2.23:1（要求 3:1）。
   修法是让 outline-color 走 `--cn-accent-text`（画布 5.49:1 / dark 5.76:1）；
   第一次覆盖没生效，因为赢下 specificity 的是 `button:focus-visible` 而不是
   `:focus-visible`——补上该选择器后 8 组对比度 + 双主题 focus 全 0。
2. **truth_baseline.log**：v1 包 README 声称有、实际没打进 zip，所以基线对照无法独立复算。
   v2 包已包含 `truth_baseline.log`（762/0）与 `truth_patched.log`（827/0），
   README 清单与 zip 内容逐条核对一致。
3. **MapPanel 的行为 delta**：`failIfMajorPerformanceCaveat: false` 连同解释它的注释
   （"瓦片服务不可达时别让用户对着空盒子看，受限网络很常见"）被 Apple 分支的 GeoJSON
   typing 修复一起删掉了。maplibre 自身默认确实是 false，行为可能等效，但这条注释承载的是
   产品意图，不该藏进"前置类型修复"四个字里 —— 已把该行与注释恢复回源码，
   并在此处明列为 reconciliation delta。

## 11. 下一轮范围（照裁决，不扩面）

Apple 线只做 #1 重复语言入口、#2 Today CTA 层级（有 active journey 时唯一 primary 是
"查看实时行程"，"AI 帮我规划"降级、"试用其他城市"归创建路径、"打开行程工作台"降 tertiary）、
#3 Live 次级动作层级（Current → Map → Disruption/Replan → 更新位置·报告降雨 → mode/evidence）、
#4 地图诚实空态高度；主线做 #5 Copilot 遮挡（统一 bottom clearance）、#6 avatar 溢出、#7 文案粘连与
`transit` 未本地化；测试债做 8 条 legacy 的 capability mapping 与 4 条当前 V8 规格重写。
Trips / Copilot 主页面 / Onboarding 继续不碰。

---

# pass-9 收口（按裁决范围，不扩面）

## 12. Apple P0 四项

| # | 裁决 | 落地 |
|---|---|---|
| 1 | Today 重复语言入口 | 删掉 hero 区的 `home-language`（topbar 已拥有该控件，全仓无其它引用）。 |
| 2 | Today 唯一 primary | `AI 帮我规划 / 试用其他城市 / 打开行程工作台` 从四个堆叠全宽按钮变成一行 quiet 文本动作（`.v8-hub-actions` 此前**在仓库里根本没有 CSS 规则**，这就是它们渲染成"按钮联合国大会"的直接原因）。门同步升级：旧断言只数 hero **内部**的 primary，所以紧贴其上的全宽 `.v8-primary` 门是看不见的；现在要求整屏可见 primary ≤1 且必须是 `today-hero-cta`。**非空过已证明**：把 `hub-plan-with-ai` 改回 `.v8-primary` 立刻 FAIL 并点名两个按钮。 |
| 3 | Live 次级动作层级 | `更新位置 / 报告降雨` 移出 Live intro，落到 Disruption/Replan 之后的 compact 行，顺序成为 Current → Map → Disruption/Replan → utilities → mode/evidence。 |
| 4 | 地图诚实空态高度 | 第一次修完全无效：Apple 的 240/208 规则带 `!important`，而 CSS 里 **min-height 优先于 max-height**，盒子仍是 240px。在同一 register 里豁免后 97px，Live 地图带从 2065px 页高压到 228px。 |

门侧诚实化：`qoder-live-structure` 现在打印它量的是哪个分支
（`[live-map] branch=honest-empty-state height=97px`）。曾尝试给 mock 加坐标去真正验证 240/208
分支，结果 maplibre 开始拉 style/tiles，离线 harness 直接挂起、dark 审计还把地图 canvas 算成违规 ——
已回退并写明"该分支需要联网环境"，而不是留一条时隐时现的绿灯。

## 13. 主线三项（单独提交，归属清楚）

- **#5 Copilot 遮挡**：`.v8-content` 统一预留 `124px + safe-area` 底部带；决策态 dock 收成右对齐 pill
  （原来 yield 后仍是 230px 宽横条，正好盖住全宽 Accept）。注意第一版把留白加在 `.v8-page` 上，
  而 Today/Live 会连续渲染多个 `.v8-page`，每个都加 124px，把决策块推下去 124px —— 首屏门以 8px
  之差抓到。门侧同时把"是否遮挡"改为在**决策被滚到视口中央**时测量：`scrollIntoViewIfNeeded`
  会把按钮留在视口底边，而那正是 pill 所在的位置，旧断言其实是在赌滚动位置而不是在设计保证。
- **#6 avatar 溢出**：加 `overflow/nowrap/flex:none`，两字符不再压在圆外。
- **#7 文案与本地化**：advisory 的 text 与 hint 由 inline 相邻改为块级（消除
  `每人每天约 ¥500这是按你的预算…`）；Live 的 leg 行原本把 provider 枚举原样插进中文句子
  （`transit`），现在走 `modeLabel()`，与全站其它 mode 呈现一致。

## 14. 种子升级：从"能跑"到"跑的是真东西"

`demo/reset` 给的是一天 CNX-DEMO 行程，stay-aware optimizer 返回 **0 个 option**。这个事实悄悄污染了
之前所有在它上面得出的判断：Stay Explorer 只能显示空态、恢复链没有可保护的住宿、Today 只有一天
时间线、地图永远没有 marker。种子改为通过产品 API 建两晚 CN-TIANJIN 行程并真实 generate + select：
`options=4 chosen=… (Haihe Riverside Hotel)`、`trialWizard=false`、`live-journey-current=true`，
地图第一次渲染出真 marker。

它立刻抓到三个此前不可见的缺陷：

1. Today 在真实 disruption 下出现**第二个 primary**（attention band 的 `Review in Live`，与 hero 同目标）
   —— 裁决 #2 的第二个实例，已降级。
2. `current` 地图 marker 白字 10px on `#d65e56` = **3.75:1**。改用 `--cn-accent-solid`（两主题都是
   `#0a66ff`，白字 4.82:1）；第一版用 `--cn-accent-text`，在 dark 下 `#0a84ff` 只有 3.49:1，
   双主题门当场拦下。
3. 多日时间线的 `DAY n` 与副文本灰（`#9aa4b3` 2.52、`#6c7889` 4.48/3.8）此前从未被审计到，
   因为根本没有多日卡片。统一到 `--cn-ink-secondary`。

## 15. 门禁与套件现状

- `qoder-*` 29 条全绿；contrast 在 Today/Live × light/dark × 390/1280 **全部 0**，
  focus ring 也改成两主题都量（改名 `qoder-contrast-audit` 后立刻发现 light 下 4 条
  `button:focus-visible` 的 `#9aa8ff` outline 只有 2.05–2.23:1）。
- 全量 Playwright：31 passed / 15 failed。其中 8 条是已定性的 `/` legacy（见
  `docs/LEGACY_E2E_MIGRATION.md`），4 条当前产品 spec 已按现状重写（locale 固定、
  `hub.title`→`today-heading`、`AI`→`Copilot`、`read-only ready`→`available offline`、
  硬编码 4 张 offer 卡改为记录分支、AgentComposer testid→Copilot dock）。
- **新发现的测试基建缺陷**：`v10-inbox / v10-quality-budget / v10-accessibility` 固定 locale 后
  单跑 9 秒 4 passed，放进串行全量又红 —— 因为整套共用一个后端与一个 SQLite journey，
  前面的 spec 会 reset / 重新 select。没有靠调整顺序掩盖，作为独立缺陷记录。

## 16. 截图里仍然看得见、但我没有动手的

1. 真地图渲染后，地图左半约 40% 是未加载瓦片的浅灰底（右侧天津城区正常）—— 视觉上不平衡，
   但属于瓦片可用性/地图视野问题，不是配色。
2. 5 号 marker 被"路线上下文 · 8 段路程"信息条压掉一半。
3. dock 在 Today 首屏仍会压住 hero 之后的内容（已预留底部带，滚动后可完全避开；
   是否要在首屏就完全让位属于产品取舍）。

请复验这三条的归属，以及 pass-9 的四项 P0 是否达到
`FRONTEND_APPLE_PASS1_VISUALLY_ACCEPTED_FOR_MERGE`。

## 17. 我自己在收尾期间造成并已修复的事故（如实记录）

清理两个临时对照 worktree 时用了 `git worktree remove --force`，而它们的
`node_modules` 是我先前用 **Windows junction** 指向集成树
`_qoder_integration_20260919/frontend/node_modules` 的。删除过程把集成树的
`node_modules/.bin` 一起抽走（375M / 389 项，`tsc` 与 `vite` 消失，`npx tsc`
开始去下载一个叫 `tsc@2.0.3` 的无关假包）。

处置：从 `D:\moodle\_qoder_th_20260918\frontend\node_modules` 用
`robocopy /E /XO` 补齐回 409M，并在同一 HEAD（`7870270`，工作树 0 行改动）上重跑：

| 检查 | 结果 |
|---|---|
| `tsc -p tsconfig.typecheck.json --noEmit` | 0 错误 |
| `vite build` | 通过（7.16s） |
| `npx playwright test e2e/qoder-*` | 29 passed |
| 后端全量（同环境、独立 DB） | 827 passed / 15 skipped / 0 failed（68.5s） |

教训与遗留：

- **junction 不能当 worktree 的 `node_modules` 来源**；要隔离就得真复制。
- 两个残留空壳目录（`_qoder_a_only`、`_qoder_truth_baseline`）已安全清掉：先用
  `os.rmdir` 删除 reparse point 本身（它不跟随链接），确认两个真实
  `node_modules` 仍是 409M / 399 项之后，才 `shutil.rmtree` 删壳目录。
  直接 `rm -rf` 会顺着 junction 再咬一口，这一步不能省序。
- 其它 lane（Astra / Sol）被裁决为把我的树当只读输入，所以这条恢复记录也写给它们：
  当前 HEAD 的工具链与门禁状态是完好的，上面四项可复现。

---

# pass-10 极窄 closeout（按 pass-9 裁决的五条，不扩面）

## 18. 四条 blocker 的结果

| blocker | 裁决要求 | 落地 | 证据 |
|---|---|---|---|
| 1 marker 被 route-context 压住 | 不许 z-index 互相霸凌；要让地图知道 overlay 占了空间 | fitBounds 的 padding 从统一 42 改为实测 caption 高度 + 16px 安全间隙（只加大 bottom） | live-412x915-light.png：5 号 marker 完整可见，未被信息条截断 |
| 2 Today 大 dock 压内容 | idle -> compact pill；active conversation / meaningful task -> expanded dock | CopilotDock 新增 idleCompact = !open && !sending && !yieldToSurface，复用决策态已验证够用的 pill 形态（暴露 data-idle-compact 供断言） | 同批截图里 dock 已是右下角小胶囊；底部导航仍保留 Copilot 入口，不再双重邀请 |
| 3 半灰地图定性 | 等 style loaded + idle + 记录 tile 错误后再拍，据此分类 | capture-visual.mjs 加 tile 请求监听与静默等待（quiet 1.5s / 上限 20s），每屏输出 tiles/failed/settled/waited | 16/16 屏全部 settled 且地图完整 -> 之前那帧半灰是 harness 抢拍，属 evidence timing，结案。**但每屏仍有 6-12 个 tile.openstreetmap.org 请求失败**（本网络不可达），说明"瓦片源不可达时 canvas 留灰区"是真实产品韧性缺口，不是截图问题 |
| 4 E2E journey 隔离 | 每 spec 自建 journey / 自持 journey_id / 自设 localStorage；不许调顺序或 retry 掩盖 | 新增 e2e/_qoderFreshJourney.ts（只走公开 API，两晚 CN-TIANJIN），接入 v10-inbox、v10-accessibility、v10-quality-budget、product-v8 | 全量 31 passed / 15 failed -> 35 passed / 11 failed；恢复的正是"单跑绿、全量红"那四条 |

## 19. 还没消掉的跨 spec 污染（如实上报）

qoder-live-structure 的 map-height 门：单跑 7 秒 2 passed，放进全量就红。
所以 blocker 4 是显著缓解而非结案——整套仍共用一个 SQLite 文件，任何写状态的 spec
都是共享资源。裁决里提到的下一步（per-worker / per-suite 临时 DB）我没有做，因为它要改
harness 的启动方式，会波及 Codex Sol 与 Astra 两条 lane 的只读输入约定，应该由你决定
是否在这个时点动它。

## 20. 一条自我纠错

pass-9 里我提交过一个"让 Live 的『现在』标签不再折行"的 commit，它其实什么都没改：
存在性守卫写的是子串 `.v8-live-label {`，而这个子串已经出现在深色主题的
`.v8-product-shell .v8-live-label {` 里，于是脚本判定"规则已存在"直接跳过写入。
重拍截图时才发现标签仍然两行。现在换成不会误匹配的守卫，并确认单行。
这正是你反复警告的"安慰剂修复"那一类，区别是这次是门和截图抓住的，不是我抓住的。

## 21. 请判

1. Blocker 1/2/3 是否足以签发 FRONTEND_APPLE_PASS1_VISUALLY_ACCEPTED_FOR_MERGE。
2. 瓦片源不可达时的灰区：算产品韧性 blocker，还是算环境限制（本网络无法访问 OSM）。
3. Blocker 4 的部分完成（35/11，仍有一条跨 spec 污染）是否继续挡住
   INTEGRATION_CANDIDATE_READY_FOR_MAIN，以及是否授权我做 per-worker 临时 DB
   （它会改变 harness 启动方式，影响其它 lane 的只读输入约定）。
4. 你提的"最终 release candidate 前用干净 checkout + 自己的 lockfile npm ci 重建一次"
   我留到 integration freeze 执行，不在这轮占用视觉线收口。

---

# pass-11 integration evidence closeout

按裁决只做三件事，没有扩面。

## 22. ① map-height 的真相：不是数据库污染

你的判断方向对，而且实际比"旧断言没迁移"还多一层。同一个文件里两处矛盾 + 一处竞态：

- Phase 4 仍硬断言 238–242 / 200–216，而 Phase 2 已承认无可信坐标时走 honest empty state（≤156px）。
  同一 fixture，两条互相矛盾的规则，旧的输了。
- 门还在面板**切换中**读取。诊断输出直接自相矛盾：`branch=rendered-map height=208px`，
  而同一时刻页面上那个节点其实是 97px 的 empty 面板。

现在统一成一个 helper：先等 `[data-testid=v8-map-empty]` 或真地图 canvas 出现，再读，再按分支断言。
三个 Live 状态一致报告 `branch=honest-empty-state height=97px`，因为 mock fixture 本来就没有可信坐标。
240/208 的区间**保留写在代码里但没有可达路径**（需要真坐标 + 瓦片访问），没有偷偷删掉。

顺带按你的 evidence hygiene 纠正了 `capture-visual.mjs` 的注释：它等的不是 MapLibre style/idle，
而是"看起来像 tile 的请求 1.5 秒内不再新增"（20 秒上限），而且它根本拿不到 map 实例。
证据不变，描述不再越界。

## 23. ② HEAD 与数字对齐

`COMMITS.txt` 之前只到 `f34d50e`，而报告声明 `f5117f4`——包确实不能自证。
本轮重跑并把清单、报告、README、`fe_full_pass11.json` 全部对齐到**同一次运行**：

| 项 | 值 |
|---|---|
| HEAD | `dafe091`（pass-11 ① 之后） |
| 全量 Playwright | **35 expected / 11 unexpected / 0 flaky**（stats 块原样引用，306.3s） |
| `qoder-*` | 29 passed（含 branch-aware map 门 10 passed） |
| contrast | Today/Live × light/dark × 390/1280 全 0 |
| 后端同环境 | 827 passed / 15 skipped / 0 failed（基线 762 / 0） |

之前 34/12 与 35/11 的差别来自我引用了不同次运行，这是记账错误，不是产品差异，已按单次运行固定。

## 24. ③ 三条当前 spec 的定性：全是规格漂移，没有一条是共享状态

关键实验：把这三条**单独**跑（同一 HEAD，setup 种子相同），结果与全量一致地失败。

| spec | 首个失败点 | 单跑 | 全量 | 定性 |
|---|---|---|---|---|
| `product-v8` mobile composition | `getByTestId('v8-agent-submit')` 永不出现（60s timeout） | 失败 | 失败 | **规格漂移**：AgentComposer 那套控件已被 Copilot dock 取代，`v8-agent-submit` 在 src 里不存在。我上一轮只改了 `v8-agent-composer`→`v18-copilot-dock`，漏了 submit 这一步 |
| `real-world-trip-operations-v9` | `getByLabel('Reservation JSON')` 永不出现（60s timeout） | 失败 | 失败 | **规格漂移**：`bookings.reservationJson` 这个 i18n key 还在字典里，但已没有任何组件使用它，即 bookings 页的 JSON 粘贴入口在当前产品里不是这个形状 |
| `v10-live-execution` | heading `Choose your next leg.` not found | 失败 | 失败 | **规格漂移（待定位）**：`live.title` 的 en 值确实就是这句，所以问题不在文案，而在该 spec 没接入 per-spec journey（我没把它列进 pass-10 的四条），页面停在 setup 向导。属于 fixture 归属未完成，不是产品坏了 |

**因此按你设的门槛，测试基础设施改造不该授权**：没有任何一条呈现
"同一 HEAD、单跑稳定 PASS、全量稳定 FAIL" 的形态。`workers: 1` 下 per-worker DB
本来也无效，这一点你已指出。剩下的红灯是三条规格需要按当前产品重写，
其中 `v10-live-execution` 只需补上它自己的 journey 归属。

## 25. 请判

1. ①②③ 是否构成 `BLOCKED_ON_E2E_EVIDENCE_CLOSEOUT` 的解除条件，还是仍要求我先把这三条重写到绿。
2. `v10-live-execution` 我判断是"fixture 归属未完成"，是否直接按 pass-10 的方式接入 `_qoderFreshJourney` 即可。
3. `product-v8` 的 Copilot 提交步骤与 `v9` 的预订导入入口，需要按**当前**产品形状重写断言：
   这两处涉及"当前认可的行为是什么"，我不替你定，请你或负责人给出目标断言，或者授权我按现状调查后提出草案。

---

# pass-12（2026-09-19 19:0x，HEAD `2875aba`）

按裁决只做三条当前产品规格的迁移 + 文档纠正 + 门禁复跑，没有碰那 8 条 legacy。

## 26. 三条迁移的结果，以及每条"没有削弱断言"的证据

| spec | 迁移内容 | 保留/替换掉的断言 | 非空转证明 |
|---|---|---|---|
| `v10-live-execution` | 接入 `_qoderFreshJourney`（`createFreshJourney` + `useJourney`），文案对齐现行 `exec.readOnlyReady` | 时钟、证据链断言一字未改 | 单跑 2 passed；去掉 journey ownership 会退回 `Choose your next leg.` 失败 |
| `product-v8` mobile composition | 导航改用现行 `data-testid`（`nav-agent`/`nav-trips`/`nav-me`/`nav-hub`）；Copilot 步骤改成真实交互；Bookings 走 Trips 标签页 | 旧的 `v8-agent-submit` + `Mission captured` 换成 `v15-copilot-input` → `v15-copilot-submit` → `v15-intent` + `v15-mode`；Me 屏换成 `v8-me` + 现行标题 | 你上一轮判定"断言 dock 可见"是穿了新衣服的空转，成立，已按你的意见改成**发送一句话并观察服务端回执**；`v15-intent`/`v15-mode` 只有在拿到 response 后才渲染 |
| `real-world-trip-operations-v9` | 预订录入改走消费者手工表单（`inbox-tab-manual` → 字段 → `manual-submit` → `v13-2-confirm`），钱包列表通过 Advanced 展开后核对；后半段链路切到桌面宽度 | 行李感知恢复链（`active_plan.legs == activities-1`、`LUGGAGE_DROP`/`CHECK_IN` 角色、amap `wgs84` 链接、`Location updated · accuracy 12 m`、`Autopilot recovered the exposed leg`）全部保留 | 单跑 2 passed，且 `reports/product-v9/ui/live-journey-mobile.png` 现在能看见"NEXT · LEAVE BY / Luggage drop · Haihe Riverside Hotel / NAVIGATE →"，离线截图能看见种子酒店进了 24 小时快照 |

一处**主动披露的替换**：v9 原来还断言 bookings 页标题 `Your real reservations, protected.`。
该标题属于被折叠的开发者工作台，我没有把它塞回消费者路径，而是以 `inbox-tab-manual` 与
`v10-inbox-draft` 的存在作为"到达 Bookings 面"的证据——覆盖面略窄了一点，但不再依赖被折叠的入口。

## 27. 计划外的第 9 条红灯：不是漂移，是前端套件一直在借用别人的后端

第一次全量跑出 **37 expected / 9 unexpected**，多出来的是 `v13-5-fully-grounded`。逐层定位：

1. 它**单跑也失败**，页面停在 `Composing city evidence…`，即 `expect` 的 10s 预算内服务端没返回 → 排除我这三条迁移造成的跨 spec 污染。
2. 用同样的三步直接打 API（`demo/reset` → 三次 `inbox/import`+`confirm` → `real-city/intelligence`）：
   请求 **201 成功但耗时 15.5s**，因为应答的 `:8000` 后端 `ai: enabled`，语义组合走 DeepSeek，而校园网出口当前很慢。
3. 根因是环境归属：`_qoder_integration_20260919` **没有自己的 venv**，`playwright.config.ts` 的
   `backendPython` 因此退化成系统 `python`（3.10，`ImportError: StrEnum` 起不来），而 `reuseExistingServer: true`
   让套件静默复用了 `:8000` 上那个由别的 lane 起的进程（命令行是 uv 的 cpython-3.12，不是本仓代码）。
   也就是说：**过去几轮"前端 e2e 通过"的证据，后端可能根本不是被集成的那份代码**，AI 开关和数据库也不由这次 HEAD 决定。
   这同时解释了"同一 HEAD、不同数字"（34/12 → 35/11 → 37/9）。

受控复现（本轮权威数字的来源，未改任何 harness 代码，只是显式给环境）：

```
DEEPSEEK_API_KEY= CITYNEXUS_AI_API_KEY= CITYNEXUS_AI_ENABLED=false \
CITYNEXUS_PYTHON='D:\moodle\CityNexus\.venv\Scripts\python.exe' \
CITYNEXUS_BACKEND_PORT=8021 CITYNEXUS_E2E_PORT=4194 \
CITYNEXUS_DATABASE_URL='sqlite:///./_p12_full.db' \
  npx playwright test --reporter=json
```

结果：**38 expected / 8 unexpected / 0 flaky**，与你预测的分毫不差，且 8 条正是已分类的 legacy 8 条。
`v13-5` 在该环境下通过。
*（pass-13 更正）* 我原来写"13.0s 通过"是记账口径错误：13.0s 是那次 `npx playwright test` 的整条命令墙钟
（含两个 webServer 启动与 `real-seed` setup 项目），`fe_full_pass12_isolated.json` 里 `v13-5` 自身的
result duration 是 **1221 ms**。真正慢的是借用 `:8000` 那次的外部 AI 路径（另行直调端点约 15.5s，
测试自身 10990 ms 后在 10000 ms 预算上超时）。两个数字分属不同层，不该混着引用。
两次运行的 JSON 都进包（`fe_full_pass12_shared8000.json` 与
`fe_full_pass12_isolated.json`），因为前者本身就是这个环境归属缺陷的证据。

## 28. 门禁数字（全部来自同一次受控运行，HEAD `2875aba`）

| 门禁 | 结果 |
|---|---|
| 全量 Playwright | 38 expected / 8 unexpected / 0 flaky（188.8s，`workers: 1`） |
| 其中 `qoder-*` | 28 passed / 0 failed（同一 JSON 按文件聚合，见下表） |
| 其中两条对比度门 | `qoder-contrast-audit` 4 passed、`qoder-live-structure` 9 passed。审计 JSON：8 屏（Today/Live × light/dark × 390/1280）共扫描 1740 个节点，**violations 0**；borderWarnings 每屏 2（dark）/4（light），与 pass-11 提交的 JSON 逐字节相同（本轮无视觉回归，文件未变更） |
| `typecheck` / `typecheck:all` | 0 error |
| `vite build` | 成功（PWA generateSW，precache 9 entries / 2295.48 KiB） |
| 后端同环境 | 827 passed / 15 skipped / 0 failed（58.21s，AI key 置空，主仓 venv 的 python 3.12） |

三条迁移过的 spec 在切换 HEAD 前后**单独**跑过一遍（8.6s / 15.9s / 12.4s 全绿），全量再复跑一次，
不存在"只有单跑绿"的情况。

按文件聚合（同一 `fe_full_pass12_isolated.json`，pass/fail）：

| 文件 | pass | fail | | 文件 | pass | fail |
|---|---|---|---|---|---|---|
| `_qoderRealSeed.setup.ts` | 1 | 0 | | `qoder-mobile-overflow.spec.ts` | 1 | 0 |
| `product-v8.spec.ts` | 2 | 0 | | `qoder-today-hero.spec.ts` | 2 | 0 |
| `real-world-trip-operations-v9.spec.ts` | 1 | 0 | | `v10-accessibility.spec.ts` | 1 | 0 |
| `v10-live-execution.spec.ts` | 1 | 0 | | `v10-inbox.spec.ts` | 1 | 0 |
| `v10-quality-budget.spec.ts` | 1 | 0 | | `v13-5-fully-grounded.spec.ts` | 1 | 0 |
| `v13-authoritative-integrity.spec.ts` | 1 | 0 | | `qoder-ack-rendered.spec.ts` | 6 | 0 |
| `qoder-ack-resolution.spec.ts` | 1 | 0 | | `qoder-budget-evidence.spec.ts` | 2 | 0 |
| `qoder-budget-rendered.spec.ts` | 3 | 0 | | `qoder-contrast-audit.spec.ts` | 4 | 0 |
| `qoder-live-structure.spec.ts` | 9 | 0 | | **8 条 legacy** | 0 | **8** |

`golden`(1) + `live-autopilot-v5`(1) + `predictive-real-city-v6`(1) + `product-hardening`(5) = 8，
与 `docs/LEGACY_E2E_MIGRATION.md` 的清单逐条一致，没有第 9 条。

## 29. 截图复核里新看见、我没有动手的一处

*（pass-13 更正：这条的具体结论不成立，我先自己撤回。）*

原结论写的是"Copilot 悬浮胶囊压在 EVIDENCE 卡片首行，`Provider route, fres…` 被遮住"。
把 `reports/product-v9/ui/live-journey-mobile.png` 当证据看是错的：那是一张 390×2250 的
`fullPage: true` 拼接图，EVIDENCE 那一行在图里更靠下、文字是完整可读的，并没有被盖住。
`position: fixed` 的悬浮元素在整页拼接里会落在它当时所在的滚动位置附近，所以它能证明的只有：
**Live 页的固定 pill 与"Compare all modes"一带的内容空间发生了冲突**——这仍然值得查，
但不能拿它当作"EVIDENCE 首行被遮"的证据。方法错误本身记一条：不要根据长截图的拼接结果推断
遮挡关系，也不要去改 CSS。pass-13 改用在 390×844 真实视口下取 `getBoundingClientRect()` 相交判定，
结果见 §32。

## 30. 请判

1. 环境归属：是否授权我把"前端 e2e 必须跑在本仓代码自起的后端上"变成**可检查的约束**
   （最小做法：`playwright.config.ts` 在复用已有 server 前先核对 `/health` 里的构建标识，不匹配就 fail fast）。
   这属于你此前划的"Playwright 启动/数据库改造 NOT_AUTHORIZED"边界，所以我先问不动手。
2. `v13-5` 的 10s 预算：AI 打开时该端点确实要 15s+。这是产品性能问题（应给 discovery 一个
   可等待的进度态或后端超时降级），还是测试预算问题（`expect` 单独放宽到 30s）？我倾向前者，
   因为消费者真的会盯着"Composing city evidence…"不动。
3. pass-12 三条迁移是否解除 `CURRENT_E2E_CONTRACT_MIGRATION`（`BLOCKED_ON_E2E_EVIDENCE_CLOSEOUT`
   已由 pass-11 解除）；若解除，下一轮按 `docs/LEGACY_E2E_MIGRATION.md` 的 archive/port 判定执行，
   还是先做 §29 的 Live 遮挡与 Hero→replan 路线图。

---

# pass-13（2026-09-19 20:0x，门禁树 `5e84e29`）

按裁决只做 A（authoritative provenance 门）与 C（Live dock 先验证后修）两件事，
没碰 8 条 legacy，没开 OSM/Hero 路线图，没改 v13-5 的 10s 预算。

## 31. A：把"测的是不是自己"变成机器事实

`CITYNEXUS_E2E_AUTHORITATIVE=1` 下按顺序强制：

| 约束 | 落点 | 观察到的行为 |
|---|---|---|
| `CITYNEXUS_PYTHON` 必须显式给出且文件存在，禁止退系统 Python | `playwright.config.ts` | 缺失/路径不存在 → `authoritative mode refuses to start: CITYNEXUS_PYTHON="./nope.exe" does not exist` |
| 前端与后端端口必须显式且不相等 | 同上 | 缺 `CITYNEXUS_E2E_PORT` → 直接拒绝 |
| 独立 DB，且文件名必须含本次 `CITYNEXUS_E2E_RUN_ID`，必须是 `_*.db` | 同上 | `sqlite:///./citynexus.db` 被拒；命名含 run id 使"每次全新库"成为结构性质，而不是"跑之前偷偷删一下"（globalSetup 在 webServer 之后运行，那时文件已被本 run 的后端打开并锁住，Windows 上 `rmSync` 直接 EPERM——这条我踩过并改成了结构性方案） |
| 外部 AI 必须关闭 | 同上 | 环境里留着 `DEEPSEEK_API_KEY` 就拒绝启动，而不是静默走真模型 |
| 两个 webServer 全部 `reuseExistingServer: false` | 同上 | 端口被占时 Playwright 自己就拒绝：`http://127.0.0.1:8026/api/v1/health is already used, make sure that nothing is running on the port/url or set reuseExistingServer:true` |
| 通过**前端 origin** 读 `/health`，要求回显本次 run token、DB 路径、`ai=disabled` | `e2e/_qoderAuthoritativeSetup.ts` | `provenance ok: run=p13final1 frontend=:4202 -> backend=:8029 ai=disabled db=sqlite:///./_p13final1.db`；token 不匹配时报文直接指出"应答 :PORT 的后端不属于本次调用"并给出 netstat 查法 |

为什么要绕前端而不是直连后端：测试真正依赖的是 `vite → proxy → backend` 这条链，
只有从前端 origin 拿到正确 token，才能同时证明 dev server 也是本次起的。

`/health` 为此新增 `e2e_run_id` 与 `database_url` 两个字段（`backend/app/core/config.py`、
`app/main.py`），并由 `backend/tests/test_e2e_provenance.py` 钉住三条事实：
没被盖戳的服务器回显空串（所以借来的后端永远过不了断言）、被盖戳的回显自己的值、
以及它报的是自己打开的 DB。按裁决**没有**引入 Git SHA/哈希门。

provenance 打到 stderr（stdout 留给 `--reporter=json`，否则 JSON 会被首行污染——这个我第一版就踩了），
并落盘 `reports/e2e-provenance/authoritative.json` 随包交付。
workers / spec 顺序 / retry / DB schema / 产品语义一律未动。

## 32. C：Live dock 用真实视口重测，结论是我上一轮看错了

`e2e/qoder-dock-geometry.spec.ts` 在 390×844 下取 `.cn-copilot-dock` 与视口内所有可交互元素
（`button, a[href], input, select, textarea, [role=button]`）的 `getBoundingClientRect()`，
在 top/middle/bottom 三个滚动位各测一次并打印数字，截图为非 fullPage：

```
[dock-geometry] /v8/live   @top    dock=215,706 165x54 state=collapsed idle-compact idleCompact=true scrollY=0/1318    actionableInView=21 covered=0
[dock-geometry] /v8/live   @middle dock=215,706 165x54 ...                                            scrollY=659/1318  actionableInView=14 covered=0
[dock-geometry] /v8/live   @bottom dock=215,706 165x54 ...                                            scrollY=1318/1318 actionableInView=7  covered=0
[dock-geometry] /v8/hub    @top    ...                                                                actionableInView=21 covered=0
[dock-geometry] /v8/hub    @middle ...                                                                actionableInView=18 covered=1
      button "DAY 1FridayArrival · Check in · " rect=626..782 overlap=158x54px
[dock-geometry] /v8/hub    @bottom ...                                                                actionableInView=9  covered=0
```

结论：
1. **Live 页不成立**。真实视口里 dock 已经是 idle-compact 小胶囊（165×54，位于 215,706），
   三个滚动位都没有压住任何可交互元素；`reports/dock-geometry/live-390x844-bottom.png` 里
   `EVIDENCE / Provider route, freshness, cost and feasibility` 整行完整可读。
   pass-12 §29 那句"EVIDENCE 首行被遮"是 390×2250 fullPage 拼接图的产物，已按你的判定在 §29 就地撤回。
2. **没有做产品 CSS 改动**，因为不成立；这条归 `fullPage capture artifact`。
3. 顺带量到一件需要你定性的小事：Today 在**滚动到中间**时，DAY 1 卡片按钮与胶囊有
   158×54 的瞬时重叠（滚动停止后 covered=0）。这是 fixed 悬浮件经过滚动内容的固有现象，
   不是静止遮挡，所以我只把"静止时不得压住任何可交互元素"写成断言（已通过），
   瞬时相交只报数字不判对错。若你认为 pill 在滚动中也必须让位，那是产品规则，等你下令我再动。

## 33. 门禁数字（全部来自 HEAD `5e84e29` 上同一次 authoritative 运行）

| 门禁 | 结果 |
|---|---|
| 全量 Playwright（authoritative） | **40 expected / 8 unexpected / 0 flaky**（194.8s） |
| 8 条 unexpected | 恰为已分类 legacy：golden 1、live-autopilot-v5 1、predictive-real-city-v6 1、product-hardening 5 |
| 其中 `qoder-*` | 30 passed / 0 failed（含新增 dock-geometry 2 条；此前 28） |
| `v13-5-fully-grounded` | expected，测试自身 result duration **1298 ms**（10s 预算未动，也未改 30s） |
| 对比度 | `qoder-contrast-audit` 4 passed；8 屏 1740 节点 0 violations |
| `typecheck` / `typecheck:all` | 0 error |
| `vite build` | 成功（PWA precache 9 entries / 2295.48 KiB） |
| 后端同环境 | **830 passed / 15 skipped / 0 failed**（58.6s；= 827 + 新增 3 条 provenance 测试） |
| SQLite 争用告警 | 本次 authoritative 全量 0 次（此前单规格探测时出现过 1 次 `JourneyTwin cache write skipped ... database is locked`，未导致失败，仍记录在案） |

## 34. 请判

1. Today 滚动中途的瞬时相交（§32 第 3 点）：判"fixed 悬浮件经过内容属正常"结案，
   还是要求 pill 在滚动中也让位（那就是一次真实的 yield 规则改动）？
2. authoritative 模式目前只在我这条线强制。是否把它写进 `docs/` 的验收规约并作为
   所有 lane 出 E2E 证据的唯一口径（Sol/Astra 的只读输入约定我不清楚，需要你或负责人确认）？
3. 下一轮按你的排期是 pass-14：8 条 legacy 的 archive / port-first。
   要我现在就把 4 条 "Archive" 的入口改成 `/legacy` 并逐条记录能力不变量已被现行套件覆盖的证据，
   还是先只写归档 PR、把 port-first 的 4 条留到之后？

---

# pass-13.1（2026-09-19 20:5x，门禁树见 COMMITS.txt）

按裁决只做三件：provenance 两处加固、Today dock 静止遮挡。8 条 legacy 一条没碰。

## 35. ① fresh-or-no-run：先说清楚为什么不能放在 config 里

裁决要求"webServer 启动前若目标库已存在就 fail fast，绝不自动删"。我先按字面实现在
`playwright.config.ts` 里，然后被自己的门拦下了：

```
authoritative mode refuses to start: the database for run "p131dock1" already exists at
D:\moodle\_qoder_integration_20260919\backend\_p131dock1.db
```

原因是 Playwright 会在主进程和 worker 进程里**各求值一次 config**，第一次求值后
后端已经建好文件，第二次求值自然"已存在"。也就是说 config 不是"启动前只问一次"的地方。

所以这条规则改放到**真正打开这个文件的那个进程**里：`backend/app/db/session.py` 的
`make_engine()` 在 `create_engine` 之前检查——只有被 `CITYNEXUS_E2E_RUN_ID` 盖过戳的进程
才受约束（普通 demo 服务与 pytest 完全不受影响），文件存在就抛错、绝不删除：

```
E2E run 'p131dock1' refuses to reopen an existing database at ...
An authoritative run must start from an empty file; issue a new CITYNEXUS_E2E_RUN_ID instead of deleting it here.
```

`_*.db` + 文件名必须含 run id 的命名规则保留，它正是让这条拒绝"可达"的前提。
三条行为由 `backend/tests/test_e2e_provenance.py` 钉住：盖戳进程拒绝重开、盖戳进程可以新建、
未盖戳进程不受影响。

## 36. ② /health 不再回显连接串

`database_url` 从 `/health` 移除，改为 `e2e_database_id`：只回显文件名（`_p131full1.db`），
且**只有被盖戳的 E2E 进程才回显**，其他进程一律空串。门与后端测试同步改了。
新增一条回归测试直接用最坏情况断言：把 `database_url` 换成
`postgresql://citynexus:s3cr3t@db.internal:5432/citynexus`，`/health` 里不得出现 `s3cr3t` 或 `db.internal`。

两条互相打架的注释也统一了：实测 Playwright 1.63 的 `globalSetup` 在 webServer **之后**运行
（第一版门在检查"端口是否空闲"时撞见自己刚起的 uvicorn，就是证据），
所以"必须在服务启动前完成"的检查留在 config 文件体内，"谁应答了这次运行"的检查留在 globalSetup。

## 37. ③ Today dock：你说得对，那是静止遮挡；另外这条规则还牵出导航栏

先认账：§32 里"静止时归零"是我的错误解释。middle 采样点确实是滚动停止、等了 450ms 之后测的，
重叠仍然存在；bottom 为 0 只是另一个位置的结果，我把它当成了"静止"的证据。

把门改成三个静止位都要 `coveredByDock == 0` 之后，我先加了一个**参照测量**（只报数不断言）：
同一规则套在底部导航栏上会怎样。

```
[v8/live @top   ] dock=215,706 165x54  coveredByDock=0  coveredByNav=2   nav=768..844
      (nav reference) button "mode-walk"    overlap=318x44px
      (nav reference) button "mode-bicycle" overlap=318x13px
[v8/hub  @middle] dock=215,706 165x54  coveredByDock=1  coveredByNav=2
      button "DAY 1FridayArrival · Check in ·" overlap=158x54px
      (nav reference) button "DAY 1..." overlap=356x14px  button "DAY 2..." overlap=356x36px
```

也就是说：`position: fixed` 的底部条带在任何静止位都会压住可交互内容，导航栏压得比 pill 更狠
（`mode-walk` 被盖 318×44，几乎整只按钮）。要按字面把这条规则贯彻到两者，唯一结构性做法是
把滚动视口截短到 pill 之上（导航 76px + pill 54px + 间隙 ≈ 138px），等于每台手机永久让出约 16% 高度，
而且会直接挤压首屏门。这个代价我判断不该由一次遮挡收口来付，所以按你允许的 yield 思路做：

**pill 在静止时若压住任何可交互元素，就自己让出内容列（向右滑出），带内一空就回来。**
`CopilotDock` 里 debounce 220ms 后按**布局盒**（不是 transform 后的矩形，否则会自激振荡）判定，
CSS 只加一条 `.idle-compact.yield-at-rest { transform: translateX(calc(100% + 16px)); opacity: 0; pointer-events: none }`，
带 `prefers-reduced-motion` 降级。没有保留 `idleCompact` 之外的行为改动，没有动导航，没有重开 Apple 视觉线。
入口不丢：底部导航本来就有 Copilot 项。

修后门里的数字（同一次 authoritative 运行）：

```
[v8/hub @middle] dock=396,706 165x54 state=collapsed idle-compact yield-at-rest yieldsAtRest=true coveredByDock=0
```

其余静止位 `yieldsAtRest=false`（本来就没压东西），`coveredByDock` 全为 0。
`yieldsAtRest` 与 `coveredByNav` 都打进日志，是为了让"绿"能区分"让位生效"与"根本没重叠"。
导航栏那两处重叠我没有修也没有断言——那是 shell 级布局策略，要不要为它让出 138px 由你定。

## 38. 门禁数字（同一次 authoritative 运行）

| 门禁 | 结果 |
|---|---|
| 全量 Playwright（authoritative） | **40 expected / 8 unexpected / 0 flaky**（195.7s） |
| 8 条 unexpected | 与 pass-13 完全相同的 8 条 legacy，一条没多一条没少 |
| `qoder-*` | 30 passed / 0 failed（含收紧后的 dock 门 2 条） |
| SQLite 争用告警 | 0 次 |
| `typecheck` / `typecheck:all` / `vite build` | 全部干净 |
| 后端同环境 | **834 passed / 15 skipped / 0 failed**（58.2s；= 827 基线 + 7 条 provenance/新鲜度测试） |
| 默认（非 authoritative）模式 | 回归通过：`authoritative=false ... reuseExistingServer=true` 照常工作，并把借用状态打印出来 |

一处随行为改变而变化的证据：`reports/contrast-audit/contrast-audit-mobile.json` 里
`live/mobile/light` 的 `borderWarnings` 从 4 变成 3（violations 仍为 0）。原因就是 §37 的让位——
静止时那个 pill 不再停在原处，被边界规则量到的元素少了一个。这是行为变化的正常后果，不是审计脚本被改。

## 39. 请判

1. 底部导航栏的静止遮挡（`mode-walk` 318×44、`DAY 2` 356×36）：与 pill 同规则处理（那就必须决定
   是否让出 138px 视口），还是明确豁免固定导航条、只把规则用于浮层？我给数据不给结论。
2. pill 让位用"滑出内容列"实现：可接受，还是你更希望它改为"上移到带内空隙"或直接不在移动端浮起？
3. authoritative 模式现已满足你要求的两点加固（fresh-or-no-run、连接串不外泄），
   是否正式定为 `AUTHORITATIVE_E2E_CANONICAL_GATE = REQUIRED`，并把它连同"非 authoritative 的 E2E 结果
   只能算本地诊断"写进 `docs/`？写的话我按你的措辞落文档，不改产品码。
4. 下一轮 pass-14 按 4 条 pure Archive 开工（移出默认 acceptance suite、保留源码、只针对 `/legacy`、
   不计入 merge 门、逐条留 capability→current test 映射），port-first 4 条留到 pass-15。

---

# pass-14（2026-09-19 21:4x）

按裁决四件事：canonical 规约落文档、yield 的 a11y 加固、导航终点可达性断言、4 条 pure Archive。
4 条 port-first 一条没动、一条没 skip。

## 40. A：验收口径写进 `docs/E2E_ACCEPTANCE_POLICY.md`

规约 8 条按你给的措辞落成表格，每条都标了"在哪强制"，包括第 6 条为什么必须绕前端 origin
（测试真正走的是 `vite → proxy → uvicorn`，只有从前端拿到正确 token 才能同时证明两个进程都属于本次调用）。
另外写明：非 authoritative 结果只能算本地诊断；Sol/Astra 只读别人工作树不受影响，
但任何 lane 声称"我这边 E2E 全绿"必须交 authoritative 证据；明确**不**引入 Git/SHA 哈希门。

顺带修掉两条过期注释（`_qoderAuthoritativeSetup.ts` 里"freshness 在 playwright.config.ts 强制"、
config 侧暗示存在性检查在本文件的措辞），并把端口/Python/DB/AI 的解析逻辑抽到
`frontend/playwrightEnv.ts` 共用。抽这个文件不是整洁癖：现在有两个 config，
同一套 authoritative 规则如果各写一份，下一次漂移只是时间问题——而"两份描述各说各话"正是你逐轮在抓的东西。

## 41. B：yield 的 ghost button 你抓得对

原来只有 `opacity: 0; pointer-events: none`，鼠标碰不到但键盘和无障碍树里还在。
改成同时 `visibility: hidden`（并给 visibility 一条 linear 过渡，让滑出动画仍然完整），
恢复时一切照旧。

新增窄断言 `a yielded pill is not a ghost control: hidden, unfocusable, and back again`：
先遍历若干滚动位**找到**让位状态（找不到就显式失败并提示"这条断言会空转"，而不是静默通过），
然后断言 `toBeHidden()`、JS 主动 `focus()` 也拿不到焦点、`checkVisibility()` 为 false；
最后再遍历回清晰位置，断言 pill 重新可见、可用、可键盘聚焦。
"让位后不再回来"等于删功能，所以返回路径也在断言里。

## 42. C：导航栏按你的两条规则分开处理

`coveredByNav` 从纯日志升格为**只在最大滚动位**断言 `== 0`（live 与 hub 各一条），
top/middle 继续只打印数字并在注释里写明"允许，但应该让读的人看得见"。
没有预留 138px 内容带。

## 43. D：4 条 pure Archive 是真的搬出去了

- `frontend/e2e/legacy/archived-product-hardening.spec.ts`：Control Tower evidence/authority、
  persisted NL mission、assisted acceptance、Proactive Guardian，入口改 `/legacy`，断言一字未改。
- `playwright.config.ts` 加 `testIgnore: /[\/]e2e[\/]legacy[\/]/`；`--list` 实测主套件里 legacy 目录 0 条。
- `playwright.legacy.config.ts`：显式调用才跑，打印 `NON-GATING` 横幅，
  且传 `CITYNEXUS_E2E_AUTHORITATIVE=1` 会被**报告并忽略**——归档结果不可能被误当成 merge 证据。
- 每条留下 capability invariant / 为何属 legacy / 当前 owner(API) / 当前覆盖测试 / 归档位置，
  写在 `docs/LEGACY_E2E_MIGRATION.md`；引用的 9 个测试文件与 4 条路由逐条核过存在，
  其中 twin 端点我一开始写成 traveler 级，已按实际 `GET /api/v1/journeys/{journey_id}/twin` 改正。

实测归档套件本身：`--config playwright.legacy.config.ts` → **4 passed (18.8s)**。
这条结果同时证实 pass-8 的判断：表面活着，它们在默认套件里红只是因为向根路径要了这个表面。
也因此在 legacy config 里它是绿的、在 acceptance 里不参与门，两件事不冲突。

保留在默认套件里继续红的 4 条 port-first：`golden`、`live-autopilot-v5`、
`predictive-real-city-v6`、`product-hardening`(autonomous envelope-safe)。没有 skip、没有软化。

## 44. 门禁数字（同一次 authoritative 运行）

| 门禁 | 结果 |
|---|---|
| authoritative 当前产品套件 | **41 expected / 4 unexpected / 0 flaky**（151.3s） |
| 4 条 unexpected | 精确是 golden、live-autopilot-v5、predictive-real-city-v6、product-hardening:172 |
| 与你预期 40/4 的差 | 多出的 1 条 expected 是 §41 新增的 ghost-control 断言；归档只减不加的话应为 40，我没有为了对上数字省掉这条测试 |
| `qoder-*` | 31 passed / 0 failed |
| 主套件是否发现 legacy | `--list` 22 文件 45 测试，legacy 目录 0 条 |
| 归档套件（非门） | 4 passed / 18.8s |
| SQLite 争用告警 | 0 次 |
| `typecheck` / `typecheck:all` / `vite build` | 全部干净 |
| 后端同环境 | 834 passed / 15 skipped / 0 failed（62.2s） |

## 45. 请判

1. 多出的第 41 条 expected（ghost-control 断言）是否接受为 pass-14 的正常产物，
   还是要求基线数字严格对齐 40/4。
2. `playwrightEnv.ts` 这次为共用规则做的抽取是否算越界改 harness——我判断它不改 workers/顺序/retry/DB，
   只是防止两个 config 漂移；如果你认为该留在 pass-14 之外，我可以把两文件回退成内联重复。
3. pass-15 四条 port-first 的顺序与目标断言：我建议先 `product-hardening:172`
   （envelope-safe autonomous recovery 与现行 Copilot/Guardian 面最接近），
   再 `live-autopilot-v5`（零触发）、`predictive-real-city-v6`（自主预防）、
   最后 `golden`（reload 持久化）。目标断言由你给还是我按现状提草案？

---

# pass-15（2026-09-19 22:1x）

按你定的顺序 golden → :172 → v5 → v6 做 port-first，四条都没有改指 `/legacy`、没有 skip、没有降成 API-only。

## 46. A golden：迁到当前 V8 Live，持久化用身份而不是文字

链条：closure 事件 → 当前 Live 呈现 proposal → 旅客按产品自己的 `live-accept` →
接受的 plan 身份是服务端事实（journey 与 twin 一致）→ reload 后仍渲染已解决状态 →
受保护承诺还在。断言落在 plan 身份与"不再重复询问"上，不是标题文字。

两处测量结果我没有藏：
1. **`/experience` 的 active_plan 里 6 个 activity 的 `place_id` 全是 null**，而
   `/plans/generate` 是填了 `place_id` 的。所以"同一个地点仍被保护"在当前消费者载荷里无法证明，
   我改成按旅客看得见的 title 匹配（`Nexus River Cruise Pier`），并由测试把这行差异打印出来。
   这是契约不一致，不是测试偏好。
2. 原本照 legacy 写"localStorage 键必须恰好等于三个"会因合法原因失败——Copilot dock 本来就把
   每个 journey 的对话历史存 localStorage。改成断言真正要紧的：没有任何 plan 形状的键，
   且任何存储值都不含被接受的 plan id，否则"reload 后还在"证明的是浏览器不是服务端。

setup 走产品自己的转换（demo/reset → plans/generate → select → `/start`），因为
`request_replan` 在未 ACTIVE 的 journey 上直接 409 `journey must be ACTIVE with an active plan`；
去改状态列等于测一个旅客到不了的状态。

## 47. B envelope-safe 自主恢复：数字与表面都断

legacy 用 Control Tower 的模式/成本/漂移输入。能力没消失，所以检查搬到当前表面：
gateway 在旅客自己的 policy 下 `ALLOW_AUTO`、真的 `executed`、执行出的子 plan 版本成为权威、
cost delta 与 drift 落在配置的 envelope 内、locked commitment 保住、
`/v8/authoritative` 渲染出 accepted 的子版本 id + `C4 commitments preserved` + provider 证据。
PUT 之后把 policy 读回来再断——"在 envelope 内"如果 envelope 根本没存进去就毫无意义。

实测一次：`cost delta -3000 of 5000, drift -5 of 120, plan 55523d40… -> a8f9bdc5…`。

## 48. C zero-touch：与 B 保持结构差异

触发（一个 provider 形状的 CLOSURE 事件）之后测试不做任何点击/输入/accept。
plan 身份自己改变；与该事件关联的 proposal 是 `ACCEPTED` 且 `locked_commitments_preserved`；
审计日志把它记为 `replan_auto_accepted / AI_AGENT`；`/v8/authoritative` 显示 accepted 子版本，
`/v8/live` 不再就一次已经发生的恢复询问旅客；reload 后 plan id 不变。

第一版我把 feed 请求包在 `.catch()` 里并且猜错了路径（`/agent/feed`），结果 404 被吞成空列表，
"证明它是自动的"这条断言就静默变成了空转——正是这条工作线一直在抓的沉默削弱。
正确端点是 `/journeys/{id}/agent-feed`，返回 `{source, events}`，swallow 已去掉。

## 49. D 预测式自主预防：能力在，表面没有主人——留红

后端确实端到端做了预防：只喂一个 `RISK_FORECAST` fixture（journey 上没有任何 CLOSURE/CRITICAL 事件，
这条是被断言的而不是假设的），autopilot 自己产出
`decision=PREEMPTIVE_RECOVERY / trigger_kind=PREDICTIVE / action_status=EXECUTED`，
`evidence.observation.forecast_before_hard_failure=true`，plan 从 `55523d40…` 变成 `e8037cd1…`，
River Cruise 仍在，且 `scanRequests == 0`（测试自己没去要决策，否则就成 reactive）。

但渲染它的组件——`guardian-decision`、`guardian-predictive-resilience`、`guardian-provenance`、
`guardian-trace`、`guardian-standing-mission`、`guardian-provider-risk-forecast`——
**只存在于 `src/main.tsx`，即 `/legacy` 后面的旧表面**。V8 里没有任何面承接预防结果
（`api/citynexus.ts` 有 `PREEMPTIVE_RECOVERY` 与 `trigger_kind` 类型，组件层零引用）。

因此这条按裁决**留红**，失败信息直接写 `PRODUCT INTEGRATION GAP: …` 并给出修法方向
（给 V8 一个预防结果的 owner），同时写明两条禁止的捷径：不得改成 backend-only 断言变绿，
不得把 reactive recovery 改名冒充 prevention。

一个诚实的弱点：这条断言目前是"页面文本里出现 PREEMPTIVE/predictive/forecast 之一"。
它现在为假所以缺口成立；但如果将来有人在无关文案里写了 "forecast"，它会虚假变绿。
给 V8 补真 owner 时应把这条换成结构化断言（具体 testid + run 身份），我在 §51 请判里提出。

## 50. 门禁数字（同一次 authoritative 运行）

| 门禁 | 结果 |
|---|---|
| authoritative 当前产品套件 | **44 expected / 1 unexpected / 0 flaky**（122.2s） |
| 唯一 unexpected | `predictive-real-city-v6` —— §49 的产品缺口，故意留红 |
| 与你预期 45/0 的差 | 一换一成立（45 条总数不变），差的那 1 条正是 D：能力存在、表面没有主人 |
| 默认套件是否发现 legacy | 否（`--list` 与本次运行都不含 `e2e/legacy`） |
| `qoder-*` | 31 passed / 0 failed |
| SQLite 争用告警 | 0 次 |
| `typecheck` / `typecheck:all` / `vite build` | 全部干净 |
| 后端同环境 | 834 passed / 15 skipped / 0 failed（93.9s） |

## 51. 请判

1. D 的处置：批准"留红 + 报产品缺口"，并把它排成一次独立的产品补线（V8 需要一个预防结果 owner）？
   若批准，我按你的边界提最小方案：在 `/v8/authoritative` 的恢复面板上承接 guardian 预防run
   （decision + trigger_kind + 预测证据 + 为什么提前改），不改产品语义、不复活旧控件。
2. 那条文本级断言是否接受为过渡（现在为假，能证明缺口），还是要求我在补线时一并换成结构化断言？
3. `place_id` 在 `/experience` 里为 null 而 `/plans/generate` 有值——判为契约缺陷要我修，
   还是记为已知限制？它影响任何"同一地点仍被保护"的当前表面证明。
4. 四条 port-first 已清三条，剩 D。`INTEGRATION_CANDIDATE_READY_FOR_MAIN` 的签发条件现在是否可以
   定义为"authoritative current-product 0 unexpected + D 有 owner"，还是另有条件？

---

# pass-16（回应 §51 请判 1/2/3）：身份契约、真承诺、预防的表面主人

## 52. C `place_id`：先诊断到层，再修那一层

§51.3 那个"`/experience` 里 place_id 为 null"的问题判为契约缺陷并修掉。诊断是一次测量，
不是猜测：同一次运行里，canonical 子计划 `GET /api/v1/plans/{id}` 报 6/6 活动带 place_id，
同一个计划经 `GET /journeys/{id}/experience` 报 0/6。
所以身份没有丢在 solver 或 accept 里，是丢在**投影层**。

修在 `backend/app/stay_mobility.py::_active_plan_payload`：把 `place_id` 和 `city_service_id`
放进活动投影。回归不是"字段存在"这种断言，而是整条链
（generate → select → start → closure → request_replan → accept）跑完后比较两个投影的
place_id 集合，`backend/tests/test_qoder_activity_identity_contract.py`，2 passed。
第二条测试防的是反向偷懒：替代活动也必须带真 place_id，不能靠 null 蒙过比较。

前端四条 spec 里所有 `/river cruise/i` 之类的标题匹配全部换成 place_id + protected。
标题可翻译、可改名，不是键。

## 53. A/B 承诺：fixture 里原本没有可保护的东西

写 §48 时我用了 `locked_commitments_preserved`。测量结果说明那三个案例都是空转：
demo 计划上的游船活动是 `locked: true` 而 `protected: false`——`protected` 由 ACTIVE
Commitment 行推导，必须有 booking 且付款已 CAPTURE。也就是说"受保护承诺被保住了"
在一个根本没有受保护承诺的 fixture 上恒真。

现在三条（golden / envelope / zero-touch）加上预防案例，都通过公开端点先建真承诺：
`POST /bookings` → `POST /transactions` CAPTURE（带 `Idempotency-Key`），
而且必须在 `/start` 之前——行程中预订活动会被 422 拒绝（这也是测出来的）。
共享 helper `protectCommitment()` 放在 `frontend/e2e/_qoderFreshJourney.ts`，
它建完会回读 `/experience`，若 `protected` 没落地就抛错——四个各写一份、
各自漂移成"大概受保护"正是仲裁要我避免的事。

## 54. 一条我没能证明的主张，如实撤回

预防案例里我加了"预防后的计划必须含 `real-place-*` 活动"，想证明预防 grounded 在真实城市。
**跑出来是假的**：`place-tech-art → place-city-park`，六个活动仍是 demo 命名空间。
原因也是查出来的：pytest 版 `test_v6_predictive_real_city.py` 之所以有 real-place，
是因为它用 `seed_explicit_mobility` 把特定 leg 声明成显式 replay 事实，改变了 solver
认为可负担的替代集；不带那层种子的真实 mobility 下，预防买到的是时间余量而不是换点。
在这里硬断言就是在测 fixture，不是测产品。所以删掉该断言，改成两条可证的：
`/provider-mesh` 必须含 `openstreetmap-replay` 的真城市候选，
以及把 recomposition 前后 (place_id, start_at) 指纹打进运行日志。
`v13-5-fully-grounded` 才是"真地点被选进计划"的所有者，这条不抢它的活。

## 55. D/E 预防的表面主人（§51.1、§51.2 的处置）

新增 `frontend/src/features/recovery/V14PreventivePanel.tsx`，挂在 `/v8/authoritative`
的反应式恢复面板之上。它读的是 `GuardianRun` 本身而不是计划 diff，这样就不可能把
reactive recovery 换个标签冒充 prevention：TRIGGER 行是 run 的 `trigger_kind`，
TIMING 行是 `evidence.observation.forecast_before_hard_failure`，FORECAST 行是 run
据以行动的那张快照，PLAN 行带 before/after 两个计划 id 的 data 属性，
并显式写明"反应式结果由下面的面板负责"。

§49 承认的那个可被无关文案骗过的文本哨兵已删除，换成按 testid + `data-run-id === run.id`
的结构化断言。案例同时要求：跑动前无 CLOSURE/CRITICAL、真实 forecast payload 的
`components.forecast_risk === 88`、`solver.kind === ORTOOLS_CP_SAT_V2`、承诺按身份仍在且
仍 protected、`scanRequests === 0`。

两个只有真跑才暴露的事实：
1. 韧性**总分饱和**——提交 forecast 88 渲染成 `risk 100`，所以面板和测试都看
   `forecast_risk` 分量，不看总分；
2. `GuardianRun` 行先以 `status=RUNNING / action_status=PLANNING` 落库，重排完才变 EXECUTED。
   只 poll"行出现"就会读到半成品并按 PLANNING 失败——补了一条按同一 run id 等终态的
   poll，两条失败信息各自准确（从未出现 vs 出现但没完成）。
3. 面板发现 run 后停止轮询：run 是持久证据，继续 3 秒一次只是和 autopilot 的写抢 SQLite。
4. 裁决明确"不能只凭 `trigger_kind=PREDICTIVE` 认定 grounded real-city 预测"，所以案例直接读
   run 自己的证据：`evidence.prediction.evidence_provenance` 必须非空、**每一条**都是
   `provenance == "REPLAY"`（不是被洗成硬事实的 mock 默认值）、且至少一条来自 replay provider。
   实测这张 journey 上是 `open-meteo-replay`(CITY_SIGNAL) 与 `city-signal-fixture`(MOBILITY)，
   两条都 REPLAY，mesh 里 3 个真城市候选；这些数字随运行日志一起打印，主张和数据同处一地。
   另需说明一个未消除的现象：单独反复跑这条案例时出现过 2 次
   `JourneyTwin cache write skipped … database is locked`（后端显式捕获的容错路径，不影响断言），
   而三次全量 authoritative 运行都是 0 次。我没有把它"修成 0"，只是如实报两种观察。

## 56. 归档套件的一个真实不确定性（新发现，非门禁）

legacy 套件带 host `DEEPSEEK_API_KEY` 跑：3 passed / 1 failed，
`Proactive Guardian …` 得到 `action_status=MODEL_NO_MUTATION`。
同一棵树关掉 AI 开关跑：4 passed / 21.2s。
所以那一条依赖外部模型回合，不是本轮改动引入。归档套件不签门禁，
但它的数字以后必须连着 AI 开关状态一起报——已写进 `docs/LEGACY_E2E_MIGRATION.md`。

## 57. 文档与事实对齐

`docs/E2E_ACCEPTANCE_POLICY.md` 的 "Known-red by design" 列着四条现在已绿的案例，
`docs/LEGACY_E2E_MIGRATION.md` 结尾还说它们"still red, deliberately"。两处按现状改写，
并保留原则（红测试命名缺口 > 绿测试掩盖缺口）与将来留红时的写法要求。

## 58. 证据卫生：一张"通过却空白"的截图（本轮自查发现）

第一次 authoritative 全量跑（`p16full1`，tree `6311382`）是 45/0，但我按惯例去比对
门禁重截的 PNG 时，`reports/product-v13.5/fully-grounded-discovery.png` 从 133910 字节
掉到 91550 字节。看图：页面只剩发现表单，结果卡片整块不见。
而这条 spec 是 **passed** 的——`v13-discovery-result`、`FULLY GROUNDED`、`valhalla`、
`SELECTED` 全部断言过。

原因不是功能退化，是**截图时机**：结果卡片淡入，而 `toBeVisible()` 在 opacity 0 就已经为真。
上一轮恰好截在半透明（图上能看见卡片但发灰），这一轮截在淡入之前（完全空白）。
一张在过渡中拍的图不是"已稳定表面"的证据——这正是 §29 那次 fullPage 假证据的同类错误，
只是这次藏在通过状态里。

修法（`1d922ef`）：截图前等该子树的动画进入终态，作用域限定在结果卡片，
因为应用别处有无限循环的 pulse 点，文档级等待永远不收敛。修完这张图 178816 字节，
内容比历史上任何一版都完整（候选列表含 `天津文化中心 · Eligible · openstreetmap-replay`、
证据面板、`FULLY GROUNDED`、`SELECTED`）。

其余 8 张 PNG 我做了像素级 diff 而不是只看字节：`mobility-sheet-desktop` 37.6% 变化
但内容同构（同一模态、同一横幅、同一五种模式数据），差异是 fullPage 画布上模态的
垂直锚点 + 时间戳 + 地图节点位置；其余在 0.02%–3.8%。没有一张变成空白。

最终一次运行（`p16full3`）又重截了一遍，所以引用那次的包里的图按同一方法再对比
（相对 `5de880b`）：bottom 0.02%、fully-grounded 0.03%、journey-hub 3.65%、
mobility-desktop 0.56%、mobility-mobile 37.14%、stay-explorer 1.72%、
trip-studio 2.60%、v9 live 0.01%、v9 offline 0.01%。
`journey-hub-desktop` 字节从 96643 掉到 67129 看着吓人，但像素只差 3.65%、
平均亮度 244.4 → 246.3，是 PNG 对文本栅格化的敏感性而不是内容消失；
空白页会是接近 100% 的差异，不是这个量级。

## 59. 门禁数字（同一次 authoritative 运行 `p16full3`，tree `967e2b2`）

| 门禁 | 结果 |
|---|---|
| authoritative 当前产品套件 | **45 expected / 0 unexpected / 0 flaky / 0 skipped**（115.6s） |
| 为什么不是更早那两次 | `p16full1`（tree 6311382）也是 45/0，但它产出的截图证据不合格（§58）；`p16full2`（tree 1d922ef）之后又加了 §55.4 的 provenance 断言，树变了。本轮只引用最后一次运行 `p16full3` |
| 与 §50 的 44/1 之差 | D 从红转绿：不是删断言，是补了表面主人；总数 45 不变 |
| `qoder-*`（视觉/对比/几何/无障碍预算） | 31 results / 0 failed（对比 4、dock 几何 3、live 结构 9、移动溢出 1、today hero 2、ack 7、budget 5） |
| SQLite 争用告警 | 0 次 |
| `typecheck` / `typecheck:all` / `vite build` | 全部干净（build 4.70s） |
| 后端套件（同环境，单跑） | 836 passed / 15 skipped / 0 failed（56.7s；比 §50 多 2 条 = 身份契约回归） |
| legacy 非门禁套件 | AI 关闭 4 passed（21.2s）；继承 host `DEEPSEEK_API_KEY` 时 3 passed / 1 failed（§56） |

## 60. 请判

pass-15 的裁决已经把 final integration gate 定义成三组条件，并把 pass-17 排成
Integration Freeze / Clean-checkout Reproducibility。所以本轮**不请求**签发
`INTEGRATION_CANDIDATE_READY_FOR_MAIN`——那条按你的定义要等 pass-17 从干净 checkout
复现之后。这里要的是 pass-16 的关闭判定与 pass-17 的验收形式。

1. D 的关闭五条件按裁决逐条自陈：real-city deterministic/replay 证据恢复（discover 在
   RISK_FORECAST 之前，`provenance == REPLAY`，mesh 有 `openstreetmap-replay` 候选，
   run 的每条 prediction 证据都是 REPLAY）；genuine C4 fixture（booking + CAPTURE，
   建完回读断言 `protected` 落地）；V8 有 preventive owner；结构化断言（七个
   `v14-preventive-*` testid + `data-run-id` / `data-plan-before-id` /
   `data-plan-after-id`，并断言页面显示的 run id 就是刚执行的那一个）；
   authoritative 0 unexpected / 0 flaky。identity contract 一侧：`/experience` 不再丢
   `place_id`，Golden 不再用 title 认亲。是否判 D = CLOSED？
2. §54 那条撤回是否接受：真实 mobility 下预防买到的是时间余量而不是换点，
   "真地点进入计划"的所有者仍是 v13-5。若你要求预防本身必须引入 real-place，
   那是产品语义线，需要另开实现而不是测试里断言——请明确是否开。
3. `V14PreventivePanel` 只挂在 `/v8/authoritative`（你批准的最小 owner 位置）。
   是否还需要在 `/v8/live` 出现，还是 live 只需要渲染被预防后的权威计划本身（案例里
   已用 `live-journey-current` 与 `/experience` 的活动身份对齐）？
4. `locked_commitments_preserved` 这个 proposal 级 flag 现在被四条案例的身份断言架空，
   后端仍产出它。是否降级为信息字段（以 plan 身份为准），还是保留为权威字段并要求
   后端也加契约测试？
5. pass-17 的验收形式请定：我理解为在临时目录 `git clone` 本分支 → `npm ci`（lockfile 驱动）
   → `vite build` → 一次 authoritative E2E（不借任何现有 server、独立端口与一次性 DB）→
   后端套件 → `git status` 干净，并把每步命令与输出打进包。若如此，pass-17 期间发现需要
   改源码才能复现的问题，按你的规则应当回炉为 pass-16.1 而不是在 freeze 里修，确认这一点。
6. §58 的 settled-before-capture 我只修了暴露出来的那张。其余 8 张做了像素 diff 确认未退化，
   但它们的 spec 没有同样的等待。是否推广为截图门通用前置（我倾向推广，但那属于宽泛视觉线，
   你两次让我不要重开，所以先问）。

---

# Sol Truth Convergence Integration（外部 handoff：Codex GPT-5.6 Sol V2）

## 61. 基线冲突怎么处理的（先说清楚，免得审计重新推导）

handoff 写的基线是 `HEAD = 0af1905`，并且"Do not work on the pass-15 /experience
place_id contract defect / predictive V8 ownership"。但同一份 handoff 又要求
"Preserve all current pass-15 behavior"，而 pass-15 的 GPT 裁决把那两项判为 main
前必修并已派给我——我在收到 handoff 之前已经做完、打包、送仲裁。

所以我的处置是：**不回退、不 cherry-pick、叠加在 `fec2204` 之上**。
理由是可核实的：Sol 那四项缺陷（cursor 语义、同 proposal 竞态、竞争 proposal、
CAPTURE vs ACCEPT）我逐条读过代码定位，我的五个 pass-16 提交完全没碰
cursor 解析 / accept / CAPTURE / serialization 路径，四项缺陷在 `fec2204` 上依然
全部成立。回退到 0af1905 只会把已交付的仲裁项丢掉，不会让 convergence 更好做。

Sol 的两个 verification commit（`c19daa54`、`776be4e9`）在本仓与主仓都不可读，
只在 `D:/moodle/_codex_sol_extreme_v2_20260919/snapshot/citynexus/.git` 里可读。
我只把它们当行为参考读，**没有 fetch、没有 cherry-pick**；本 pass 的实现是自己写的
（`concurrency_guards.py`、`commitment_remap.py`、`_execution_truth` 的三分支、
前端 `liveActivityWindow`），命名、注释、边界都按本线的情况写。

## 62. A / CX-SOL-001：cursor 从"提示"变成"断言"

改前 `_execution_truth`（`backend/app/operations/v9.py:129-138`）只有一条分支：
`current_index is None` 就回退到首个非终态活动。也就是说"cursor 为空"和"cursor
指向一个不在本计划里的活动"走同一条路，后者会凭空造出 Now / Next / NextLeg。

现在是三态：`VALID`（精确指向该活动）/ `ABSENT_FALLBACK`（合法前置执行态，允许回退）
/ `STALE`（present-but-unresolvable，Now/Next/leg 全为空，`now_state=STALE_CURSOR`）。
`cursor_status` 随每条投影输出：offline snapshot、Edge journey-snapshot、`/experience`。

写测试时测到的事实（不是我推测的）：`journeys.current_activity_id` 和
`activities.place_id` 都是外键，所以随机 uuid 和编造地点在 SQLite 层就被拒——
"unknown cursor" 的真实形态是**指向另一个计划上确实存在的活动**，它满足外键却对
当前计划不可解析，测试因此改成那个形状。

Edge 侧原来在 cursor 不可解析时说 `"Journey complete"`；这是假话（旅程在进行，是记录
自相矛盾），现在说 `Execution position unresolved` / `Next step unavailable`。
前端 Live 与 LiveSecondary 原来直接读 `activities[0]/[1]/legs[0]`，完全不看 cursor；
现在统一走 `liveActivityWindow`，STALE 时不再显示"Awaiting plan"（那会把旅客推去
选计划，而问题不在旅客那边），并加 `data-cursor-status` 让断言不依赖文案。
`/experience` 的活动投影补 `status`，否则客户端只能靠顺序判断"做完没有"。

## 63. B：Journey 级串行化，以及它不是什么

`backend/app/concurrency_guards.py` 新增 `journey_write_lock(journey_id)`
（RLock 注册表 + WeakValueDictionary）。边界覆盖**完整** read/validate/mutate/commit：
锁在第一次读之前拿、在 commit 之后放，并且拿锁后 `session.expire_all()`，
因为定位 journey_id 的那次读发生在锁外、不能信。接的三个写入点：
replan accept（`_accept_replan_impl` 变成 wrapper，真身在
`_accept_replan_serialized_impl`，agent gateway 走同一条实现所以自动受益）、
payment transaction 端点（commit 与 rollback 都在锁内）、以及 accept 内部的
commitment 升级。

披露按 handoff 要求做在三个地方：常量 `PROCESS_LOCAL_ONLY = True`、模块 docstring
明写"不是多 worker 安全、不是分布式安全"、以及"参考部署是单进程 SQLite 且
SQLite 不支持 SELECT … FOR UPDATE，所以没有数据库层兜底"。
以后换成分布式锁只需替换这一个函数，业务不变量不动。

## 64. C / D：接受竞态断言的是最终全局真值

`_final_truth()` 直接从行里读，不看端点：ACTIVE PlanVersion 集合、Journey 指向、
ACCEPTED proposal 集合、其 proposed_plan_version_id、锚在active plan 之外的 active
commitment、cursor 是否还能解析。每条 schedule 都过 `_assert_one_winner`。

四种 schedule（barrier 同步释放，没有 sleep 当正确性机制）：
同 proposal / 同 proposal（不同幂等键）→ 恰好一个 200 一个 409；
同 proposal 同幂等键并发 → 两个都 200 且只发生一次转换；
竞争 proposal A / B（同一 base plan）→ 恰好一个 ACTIVE，输家落在既有领域状态
`INVALIDATED`（没有为测试新增状态），其 plan 不为 ACTIVE；
replan accept / booking CAPTURE → 见 §65。

## 65. E / CX-EXT-004：CAPTURE 不再盲目升级指针

改前 `service_impl.create_transaction` 的 CAPTURE 分支全程不读 Journey、不读
`active_plan_version_id`、不重跑 gate，直接把 `commitment.activity_id` 指向的行升到
C4。并发放行后，承诺就留在被替换的计划上——旅客被告知他持有一个受保护承诺，
而没有任何权威计划包含它。

现在 CAPTURE 先解析锚点：指向的行仍在 active plan 上就直接通过；否则按结构身份
重绑，0 个匹配或 >1 个匹配一律 `CommerceConflict` → 409。
另外 accept 的重绑范围从"只有 C4"扩到"所有 active commitment"：C4 解析不了就
fail closed（拒绝整次接受），非 C4 解析不了就跳过（它不是承诺，不该因为它把旅客
需要的恢复也挡掉）。

## 66. F：三个重绑点共用一条计数规则

`backend/app/replanning/commitment_remap.py` 是唯一实现：0 → fail closed，
1 → 重绑，>1 → AMBIGUOUS fail closed。身份只比精确相等的集合
（policy 的 semantic key + 锚点活动的 metadata semantic key 为强身份；
`place_id` / `city_service_id` 为弱身份，且只在候选方没有更强语义身份时才用），
再加拉锚时刻（比较瞬时而不是字符串，因为计划按城市偏移归一化而承诺可能是 UTC）。

被替换掉的两处：accept 里的 `candidate.endswith(term)`（字符串相似度冒充身份，
短的键能声称任何共享后缀的长键）；`operations/v9.py` 激活路径的
`by_semantic.get(...) or by_place.get(...)`——匹配不到就**静默跳过**，把承诺留在
被替换的计划上，而且字典推导让 sequence 更大的活动覆盖更小的，重复身份会解析成
"最后写入的那个"。现在两处都走同一 resolver，激活路径解析不了直接 raise。

Sol 的物理身份实现**没有**移植：`compare_physical_venue()`、
`HARD_FEASIBLE_QUALITIES`、mobility provenance 与 fact-quality 规则全部保持本线现状，
`grep` 可验证它们未被本次改动触碰。

## 67. G/H：测试强度是用 mutation 检查挑出来的，不是自评

`_sc_mutation_check.py` 逐个施加破坏、跑收敛套件、还原文件。结果 **8 个破坏，7 个被杀，
1 个存活**：

| 破坏 | 结果 | 被哪些用例抓到 |
|---|---|---|
| B 锁变空操作 | KILLED | 5 条（含锁本身的对照用例） |
| E CAPTURE 不再重锚 | KILLED | 2 条 |
| A 陈旧 cursor 回退成"首个活动" | KILLED | 4 条（含投影 oracle） |
| F accept 的 C4 冲突分支被跳过 | **SURVIVED** | 见下 |
| F1 多个匹配取第一个 | KILLED | resolver 计数用例 |
| F2 零匹配返回 None | KILLED | 3 条 |
| F3 身份退回后缀相似度 | KILLED | 后缀用例 |
| F4 锚定时刻不参与匹配 | KILLED | 2 条 |

存活那一个不是我没测出来，是**它通过公开端点不可达**：把受保护地点从子计划里删掉
会被 feasibility gate 以 `LOCKED_COMMITMENT_LOST` 拒掉，复制一份会被
`ACTIVITY_OVERLAP` 拒掉，两者都发生在 remap 之前。所以该分支是纵深防御，
它的计数行为由 resolver 的直接用例覆盖。我没有为了"杀光"去伪造一个产品到不了的状态，
而是把这条写进用例 docstring 和这份报告。

mutation 检查还抓出我自己写的一条空转用例：第一版 CAPTURE-vs-ACCEPT 竞态用了
**已经 capture 过的 booking**，第二次 capture 必然 409，永远不可能留下悬挂承诺，
把锁拆掉它照样绿。改成未 capture 的 booking（accept 只重绑 C4，看不见它）之后，
它才真的能 stranded。这条也写进了提交信息。

投影差分 oracle（H）在 `test_sol_execution_cursor.py`：参考投影直接从
Activity / JourneyLeg 行重算，比较 `cursor_status`、`now_activity_id`、
`next_activity_id`、`next_leg_id`、`next_mode`、`next_eta_min`，覆盖五种 cursor
状态 + accepted replan 之后一轮；有权威事实的字段不允许任何分歧，没有权威事实时
必须 fail closed 而不是产出外观等价值。为此 `_execution_truth` 补了 `next_leg_id`
（两条 leg 可以有相同 mode 和相同 eta 却是不同承诺）。

浏览器侧新增 `qoder-stale-cursor.spec.ts`：拦截 `/experience` 注入不可解析 cursor，
断言 Live 说"未解决"而不是任何计划里的步骤，并跑同一路径的真实 cursor 作对照。
handler 里那个 `catch` 只用于页面放弃的请求，所以我加了 `served >= 2` 断言，
防止"handler 一直失败"变成静默通过。

## 68. 门禁数字（authoritative 一次运行 `scfull2`，tree `79d2098`）

| 门禁 | 结果 |
|---|---|
| authoritative 当前产品套件 | **46 expected / 0 unexpected / 0 flaky / 0 skipped**（121.1s） |
| 与 pass-16 的 45 之差 | +1 = 新增 stale-cursor 用例；没有用例被删（pass-15 的四条 port 与 D 全部保留且仍绿） |
| 后端全量 | 861 passed / 15 skipped / 0 failed（68.1s；pass-16 是 836，+25 = 本 pass 收敛用例） |
| Qoder/Sol truth contracts 子集 | 171 passed / 0 failed（12.9s） |
| SQLite 争用告警 | 0 次 |
| `typecheck` / `typecheck:all` / `vite build` | 干净 |
| legacy 非门禁套件（AI 关闭） | 4 passed（20.1s） |
| mutation 检查 | 8 破坏 / 7 killed / 1 survived（原因见 §67，非"全绿"） |

## 69. 没有做的，以及请裁

1. **Sol 的 stateful fuzz（60×30）与 catastrophic mutation campaign（17/17）没有复现**。
   本仓不存在任何 property-based / stateful / fuzz 测试（`grep hypothesis|RuleBasedStateMachine`
   零命中），Sol 的 `real_api_state_machine.py`、`mutation_runner.py`、
   `concurrency_harness.py`、`projection_oracle.py` 都在仓库之外的快照目录里。
   按 handoff"不强行凑数、行为与不变量优先"，我交了确定性并发 schedule + 差分 oracle +
   上面那 8 个破坏的 mutation 结果。是否要求把 fuzz/mutation harness 正式移植进本仓
   成为常驻门禁，请裁定——那是新增基础设施，不是本 pass 的范围。
2. CX-SOL-001 / CX-EXT-002 / CX-EXT-003 / CX-EXT-004 我的自评为
   **CLOSED / CLOSED / CLOSED / CLOSED**，证据分别是 §62+用例、§64 三条 schedule、
   §64 竞争 schedule、§65+§67；F 的物理身份按 §66 保持本线更强模型。
   请独立复核而不是接受我的自评。
3. 基线问题（§61）请确认：convergence 叠加在 pass-16 之后是否可接受；
   若要求必须从 0af1905 起算，请给出处置已交付 pass-16 的方式，我不会自行回退。
4. 与 GPT 仲裁那条线（pass-16 §60 的 5 个问题）仍未回复，两条线的裁决顺序请定。
