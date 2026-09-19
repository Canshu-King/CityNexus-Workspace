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

## 7. 请给的裁决

- A/B 整合是否接受（`FRONTEND_APPLE_PASS1_INTEGRATED_ON_TRUTH_BASELINE`？）；
- 6.1 的浅色 AA 修复与双主题门是否作为这条线的正式延续收下；
- 6.2 的 7 项视觉缺陷：哪些进入 Apple 线下一轮，哪些归主线（语言键重复、Copilot 遮挡、头像溢出
  看起来是主线既有 DOM）；
- 那 8 条 `/` 旧界面 legacy：迁移到 V8 shell 断言，还是标记为过期归档。
