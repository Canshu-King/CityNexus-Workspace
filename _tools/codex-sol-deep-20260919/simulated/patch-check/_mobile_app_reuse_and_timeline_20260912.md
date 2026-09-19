# 移动应用作业：可复用性分析 + CityNexus 项目时间线

日期：2026-09-12
依据：`01 Mobile Application Programming.zip` → `Mobile Application Programming - Assignment Coursework 2026.pdf`（原文已完整提取）

---

# 第一部分：移动应用作业能用上 CityNexus 什么

## 作业要求（原文）

| Part | 内容 | 占比 | 截止 |
|---|---|---|---|
| 1 | Mobile APP Research & Design | 50% | **2026-10-02 午夜** |
| 2 | APP Development, Debugging and Testing | 50% | **2026-11-06 午夜** |

**Part 1**：≤**6 页** PPT 转 PDF。回答六问：Who（persona：年龄/性别/偏好/退休/职业/学生/儿童/需求/触发/动机/目标）、
What（做什么）、Why（为什么选它、比同类好在哪、可否扩展）、Where（在哪用）、When（使用频率/时机/多久更新一次）、
How（是否需要专业知识）。姓名+学号写在**文件名**。

**Part 2**：
- **PowerPoint Bundle 4.1** 做的原型（iPhone/Android 模板）→ 20%
- **Mobirise 或 HTML/CSS/JavaScript** 做的网站原型（压缩 zip）→ 20%
- **报告 PDF < 2 页** → 10%：Site Map（1 页）+ 设计与开发测试说明（谁负责哪部分 / 怎么设计的 / 为什么这个风格）
  + **"为什么这个项目对作为电子工程师的你很重要"**（1 页）

**三人小组。**

## ⚠️ 两份作业同一天截止

SE 作业 Part 1 = 10-02，Part 2 = 11-06。
移动应用 Part 1 = 10-02，Part 2 = 11-06。
**完全重合。** 时间压力是叠加的，不是并行的。

## 能直接复用的（按价值排序）

### 1. Part 1 的"Why"页 —— 最值钱的一页，已经做完了

作业要求"justify why it is needed, why it's better than other APPs that do something similar"。
这一页别人最难写（要做竞品调研），而**竞品扫描已经做完了**：

- 三层市场：出发前规划（Layla / Mindtrip / 携程问道 / Google AI Mode）→ 行程中单点修复
  （VAYU / Amadeus+Microsoft / Navan）→ 行程中多约束编排+承诺保护（**未找到重合产品**）
- 核心差异化：`commitment preservation` 权重 0.24 排第一、`opportunity value` 0.06 垫底
  —— "别搞砸已有的"优先于"给你更好的"
- C1–C4 承诺分级 + `monetary_value_minor`，把"哪些事不可谈判"变成可计算硬约束

**这是整份作业里最有可能拉开差距的一页。**

### 2. Part 1 的"What"页 —— 138 条需求直接可用

对照作业列的清单，CityNexus 覆盖情况：

| 作业列举 | CityNexus |
|---|---|
| Provide information | ✅ 城市/移动/预订/上下文数据 |
| Calculate something | ✅ Contextual Journey Utility Score 八分量加权 |
| Give help | ✅ 行程中断自动恢复 |
| Use location features | ✅ MapLibre 地图、POI、路线证据 |
| Purchase things online | ✅ Booking / Order / Transaction（模拟） |
| Message others | ❌ 无 |
| Display advertising | ❌ 无 |

### 3. Part 2 的"网站原型" —— 可直接用前端替代 Mobirise

作业明确允许 **HTML/CSS/JavaScript** 作为 Mobirise 的替代。
`frontend/` 是 React 19 + Vite 7 + MapLibre + XState，**2,822 行 TS/TSX**，且：

- `src/styles.css` 有 **5 个 `@media` 断点**（760px / 560px），**已经是移动端自适应的**
- WP08 的验收门里明确写了 `mobile-width layout remains usable`
- 界面区块：Journey Operations / Agent Mode / Agent Activity Feed / Journey history /
  Replan comparison / Guardian live operations / Commitment-aware recovery

**注意**：这是一个单页仪表盘，不是多页面应用。Part 2 要的 **Site Map（1 页）** 需要
从"区块"而不是"路由"来画——这点要提前想清楚。

### 4. Part 2 的"谁负责哪部分" —— 两份作业同一个缺口

SE 作业要"Allocation of tasks i.e. who did what"；移动应用要"who was responsible for which part"。
而 `docs/implementation/implementation-status.csv` **已经有一列 `owner`，但 138 行全是空的**。
`work_packages.yaml` 也有 `depends_on`（任务关系）但没写人。

**填这一列，同时解决两份作业的问题。**

### 5. WP00–WP10 工作包分解 —— 可直接当 WBS

`_implementation_blueprint_v0.1/.../work-packages/work_packages.yaml` 里有：
**id / name / depends_on / gate** 四个字段。这就是现成的**任务 + 子任务 + 任务关系**。
SE 作业 Part 2 的项目计划可以直接基于它，补上时间和成本即可。

## 不能复用的

1. **PowerPoint Bundle 原型（20%）** —— 作业指定了特定低代码工具，React 代码替代不了，必须用那个工具做。
2. **persona（Who 页）** —— CityNexus 材料偏架构。作业要的是低门槛 persona 描述
   （年龄、性别、偏好、退休/职业/学生、需求、触发、动机、目标），**这部分需要新写**。
3. **"为什么对电子工程师重要"（1 页）** —— 个人陈述，只能自己写。
4. **Visio 用例图 ≠ Site Map** —— Visio renderer 能出 .vsdx，但 Site Map 是页面结构图，需要新画。

## 结论

**移动应用作业能复用 CityNexus 的部分，主要是"研究素材"，不是"代码"。**

- Part 1 的 6 页里，**Why 页（竞品定位）和 What 页（功能清单）几乎是现成的**，
  Who 页需要新写，Where/When/How 有素材但要压缩。
- Part 2 的网站原型**可以用前端顶替 Mobirise**（作业允许 HTML/CSS/JS），
  这是省时间最多的一项。但 PowerPoint Bundle 那 20% 必须单独做。
- 两份作业共同的缺口是**分工记录**，填 `owner` 列一次解决两个。

**最大风险**：两份作业的 Part 1 都是 10-02，且都依赖**分工**这个目前完全空白的东西。
20 天内要同时交两份 6 页/10 页幻灯片，先把组队和分工定下来。

---

# 第二部分：CityNexus 项目时间线

## 跨度：2026-09-04 → 2026-09-12，共 9 个工作日

（09-02 / 09-03 是下载课程资料，不算项目本身）

总量：88 个 review 包、20 个顶层 zip、2.5 GB、16,319 个文件、138 条需求、13 条用例、18 个实体、322 个通过测试。

## 逐日

### 09-02 → 09-03 · 前置
下载课程资料。SE 作业 PDF 09-02 14:02 落地；Mobile 作业 PDF 09-02 21:55。
`02 Software Engineering/` 与 `01 Mobile Application Programming/` 的课程 PDF 集中在 09-03 14:30–14:34 下载完。

### 09-04 18:08 · 项目起点
第一批文件出现：`use-cases/` 的 13 条用例基线 + 校验器 + schema。
时间戳高度统一（101 个文件同为 18:08:40），说明是一次批量写入。

### 09-05 01:07–02:46 · 基线冻结夜
5 次 git 提交连发（全部集中在这一夜）：

| 时间 | 提交 |
|---|---|
| 01:07 | `chore(domain): freeze CityNexus domain model v0.4.1 RC2` |
| 02:02 | `chore(domain): promote CityNexus domain model v0.4.2 RC3` |
| 02:02 | `feat(requirements): establish CityNexus requirements baseline v0.3` |
| 02:46 | `feat(use-cases): establish CityNexus use case baseline v0.1` |
| 02:46 | `feat(visio): establish CityNexus Visio model specification v1.0` |

同日出 `CityNexus-Visio-Renderer-v0.3.1-C1-Review-20260905.zip`。
**这是整个项目唯一的 git 记录——之后所有工作都没再提交。**

### 09-06 · P1 用例图布线攻坚（14 个产物）
- `CityNexus-P1-Route-Planning-Review-Package-v0.1` / `-20260906`
- `CityNexus-P1-Route-Contact-Gate-Review-Package-v0.2` / `-GPT-Review-20260906`
- 11 个 C4.x 补丁：`cnx-c41-patch` / `cnx-c41a` / `cnx-c41b` / `cnx-c41c` / `cnx-c41d` /
  `cnx-c41d-static-fix` / `cnx-c4e1-patch` / `cnx-c4extend-patch` / `cnx-c4f-validator-patch` /
  `cnx-c4fallback-patch` / `cnx-p1-contact-patch`

### 09-07 · 找到死结（11 个产物）
- `CityNexus-P1-Route-Repair-V3-GPT-Opinion-20260907`（+ continued）
- `CityNexus-P1-Topology-and-Planner-GPT-Opinion-Review-20260907`
- `handoff_20260907` / `v3_patch_20260907` / `_topology_planner_assist_read_20260907`

当日日志记录的关键结论：
- x ≈ 13.5 的南北走廊挤爆（0.28 cm 内挂了 8 条线），是 46 个接触对的主因
- `A-M-UC-08` 是一堵从 y=6.8 直穿到 11.9 的竖墙，切断所有东西向通道
- UC-10 是死结：两条线只差 0.1 cm 且必然穿过冻结线 `EXT-10-09`
- **根因：V=16 E=21 F=3 → genus=2，非平面图，当前解空间内零交叉不可能**

同日还复盘了"为什么十几轮 Codex↔GPT 外审都没做出来"，归因为角色错位、反馈循环过重、
早期决策锁死解空间、增量修补范式对全局耦合问题无效、假性接近的错觉、锚定偏差。

### 09-08 · 改动最多的一天（4 个产物）
- `CityNexus-P1-Route-Repair-V3-Codex-Review-20260908`
- `CityNexus-GPT-Deep-Assist-Review-20260908` / `_incoming_deep_assist_20260908`
- `_incoming_quota_rescue_20260908_v2`

**394 个源文件被改，是全程单日峰值。**

### 09-09 · 转向实现（29 个产物）
- MVP 实施蓝图 v0.1 落地（20 个文档 + `work-packages/work_packages.yaml`）
- 建立 WP00–WP04 工作包，检查点全部 PASS：
  `WP00.md` / `WP01.md` / `WP02.md` / `WP03.md` / `WP03_REPAIR.md` / `PRE_WP04_MINIMAL_REPAIR.md`
- 7 个 checkpoint 目录 + `docs/implementation/implementation-status.csv`（138 行状态台账）
- 评审包：`MVP-WP00-WP03-Checkpoint-Review` / `WP04-Checkpoint-Review` /
  `Post-WP04-GitHub-Integration-Foundation-Checkpoint` / `WP06-JourneyTwin-v2-Checkpoint` /
  `WP06-PostGate-Checkpoint`

**这是项目的转折点：从"画图与文档"转向"可运行的实现"。**

### 09-10 · 三套运行时（41 个产物，峰值）
- WP06/WP07 路线准备 + GPT 评审
- Provider Runtime（Gate / Hardening / GPT-Assist）
- Solver Runtime（Checkpoint / GPT-Assist）
- Weather Runtime（Checkpoint / Hardening / GPT-Assist）
- Vertical Slice Hardening + PostGoal Repair Vertical Slice
- 多个 `_fresh_*_replay_20260910` 复现验证目录

### 09-11 · 一天三个大版本（26 个产物）
- **Agent Authority V2**（Checkpoint + Final）
- **Autonomous City Intelligence V3**（Final）
- **Proactive Journey Guardian V4**（Final）
- Autonomous Product Checkpoint / Product Hardening Checkpoint
- Overnight Agent Foundation Checkpoint（v1–v4 五个版本）
- Hermes 探针 `_hermes_probe_home_20260911`
- `_fresh_agent_runtime_replay_20260911`（含 final / final2 / final3 / v3 四个迭代）

### 09-12 · 至今（12 个产物）
- **Live Journey Autopilot V5**（Final）
- **Predictive Real-City Twin V6**（Final）
- 大量 staging / replay 目录（`_v5_package_stage` / `_v6_clean_stage` / `_v6_final_stage` /
  `_v5_assist_read` / `_v6_assist_read` / `_v5_replay` / `_v6_archive_replay`）
- **Codex 仍在实时编辑**（本日 02:08–02:51 期间仍在改 `services.py` / `autorun.py` / `main.tsx`）

## 时间线特征

1. **节奏极端压缩**：9 天产出 88 个 review 包，日均约 20 个，09-10 峰值 41 个。
2. **明显的三段结构**：
   - **09-04 → 09-08**：领域建模 + 需求基线 + Visio 布线（文档与几何质量门）
   - **09-09 → 09-10**：转向可运行实现（工作包结构 + 三套运行时）
   - **09-11 → 09-12**：智能体能力快速迭代（V2 → V3 → V4 → V5 → V6，两天五个大版本）
3. **09-08 的 394 个文件改动**与 09-09 的"转向实现"紧邻——像是推倒重来的分界。
4. **git 只有 09-05 那一夜**，之后全部未跟踪，所以时间线只能靠目录命名与时间戳重建。
5. **反复出现 `_fresh_*_replay_*` 与 `-final2` / `-final3`**：说明"打包→验证→重来"是常态，
   单日最多迭代 5 次（`Overnight-Agent-Foundation-Checkpoint-20260911` 的 previous/v2/v3/v4）。

## 这份时间线对作业的直接用途

SE 作业 Part 2 要"项目计划：任务标题 / 任务 / 子任务 / **任务关系** / **资源分配与成本**"，
Part 1 要"任务分配：谁做了什么、在哪、为什么、何时、怎么做"。

这份逐日时间线 + `work_packages.yaml`（含 `depends_on`）+ `implementation-status.csv`（含空 `owner` 列），
三者合起来就是项目计划的骨架。**缺的只有两样：把日期映射到工作包，以及资源成本。**

---

# 附：哪天干的活最多（三种口径）

统计口径说明：已排除 `_fresh_*` / `_incoming_*` / `_v5_*` / `_v6_*` / `_package_*` / `_checkpoint_*` /
`review/` 等**副本与打包目录**（这些目录会保留原始 mtime，直接统计会严重失真），
并进一步区分**人手编写**与**机器生成**（`calibration/out/`、`*-report.json` 等）。

| 日期 | 人手编写文件 | KB | 活跃小时 | 交付产物 | 机器生成 |
|---|---|---|---|---|---|
| 09-04 | 26 | 132 | 2 | 0 | 1 |
| **09-05** | **169** | **850** | 10 | 2 | 18 |
| 09-06 | 93 | 587 | 13 | 14 | 39 |
| 09-07 | 7 | 30 | 4 | 10 | 81 |
| 09-08 | 45 | 305 | 9 | 4 | **363** |
| 09-09 | 97 | 350 | 13 | 24 | 0 |
| 09-10 | 63 | 265 | 10 | **34** | 0 |
| 09-11 | 78 | 585 | 13 | 23 | 0 |
| 09-12 | 40 | 666 | 4 | 13 | 0 |

## 结论

**人干活最多的是 09-05。**
169 个手写文件、850 KB、跨 10 个活跃小时（00:20–21:56），并且**当天完成了全部 5 次 git 提交**：
领域模型 v0.4.1 RC2 冻结 → v0.4.2 RC3 → 需求基线 v0.3（138 条）→ 用例基线 v0.1 → Visio 模型规范 v1.0。
扩展名分布：96 py / 44 json / 28 svg / 19 md / 16 yaml / 11 vsdx / 10 ps1 / 6 png / 5 zip。

**09-08 的"408 个文件"是假象。**
那天改动文件总数确实最高（408），但其中 **363 个（89%）是机器生成**的
`visio-renderer/calibration/out/quota_joint_20260908/eight-shard-*.json`
——是"额度救援"批次任务切了 8 个分片的输出。人手编写只有 45 个文件、305 KB。
**09-08 是"机器跑得最多"的一天，不是"人干得最多"的一天。**

**交付产物最多的是 09-10**（34 个）——Provider / Solver / Weather 三套运行时 + Vertical Slice Hardening。

**强度最高的是 09-12**：4 小时内 666 KB，约 167 KB/小时，是全程单位时间产出最高的一天（但仍在进行中）。

**最轻的是 09-07**：手写仅 7 个文件、30 KB。那天在做**只读分析**——定位布线死结
（x≈13.5 走廊挤爆、A-M-UC-08 竖墙、UC-10 死结，得出 genus=2、解空间为空）。
机器生成却有 81 个，说明当天主要靠脚本跑分析而非手写。

## 一个数据可靠性提醒

**不要用文件 mtime 直接重建历史。** 09-04 那天 73% 的文件落在同一分钟（18:08），
是批量写入；而 replay / package 目录会保留原始 mtime，导致同一秒出现上百个文件。
本次分析的做法是：排除副本目录 → 区分机器生成 → 再看时间聚集度（各日最大单分钟占比均低于 31%，
说明是真实分散作业而非一次性复制）。
