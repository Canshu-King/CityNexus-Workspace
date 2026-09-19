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
