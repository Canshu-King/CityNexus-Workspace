# TEST_RESULTS — v6（Xiaomi Truth Hardening，当前权威）

> **v6 authoritative (2026-09-19)。** 完整结论见 `QODER_V6_IMPLEMENTATION_REPORT.md`。下方 v5/v4/v2 段保留追溯。

- v6 只做 GPT v5 终裁剩下的那一个窄 blocker：把 legacy provenance 推断改成 **exact + fail-closed**。
  `_derive_fact_quality_from_provenance` 不再用 `"LIVE" in prov` / `startswith("SEALED")` 宽匹配，也不再升级
  `CAPTURED_REPLAY`/`RUNTIME_CAPTURE`；显式 `fact_quality` 永远优先，唯一可升 LIVE 的是精确 `LIVE_CAPTURE`，其余→None→拒绝。
- 为让真实捕获在无推断下仍可信，producer 侧补显式 quality：`capture_journey_mobility_matrix` 给 valhalla matrix 事实
  打 `LIVE_PROVIDER_CAPTURE`；`_grounded_recovery_reserve_snapshot` 透传源事实 quality；Tianjin replay fixture 128 条
  valhalla 事实写入 `fact_quality`。故 v12/v13/v14/v6 grounded 测试不靠推断仍绿。
- 新增针对性 legacy-label 回归（`SEALED_REAL_REPLAY_WITH_EXPLICIT_SYNTHETIC_FALLBACK`、
  `SEALED_REPLAY_OR_SYNTHETIC_FIXTURE_EXPLICIT`、`CAPTURED_REPLAY`、`RUNTIME_CAPTURE`、`SEALED_INCIDENT_REPLAY` 全 fail-closed，
  及一个 from_evidence 端到端 hard-reject）。
- 专项 focused raw log `raw_v6_focused_live_endpoint_and_provenance.log` 直接显示 L1/L2/L3/L4 各自 PASS（29 passed）。
- 严格同环境（两侧清 `DEEPSEEK_API_KEY`/`CITYNEXUS_AI_API_KEY`）：patched `2 failed(aiv3_02,v18_3) / 825 passed`
  == 干净基线两条真实失败 → **NEW-vs-基线 = ∅**。前端本轮未动。

---

# TEST_RESULTS — v5（Xiaomi Truth Hardening，权威版）

> **v5 authoritative (2026-09-19)。** 完整结论见 `QODER_V5_IMPLEMENTATION_REPORT.md`。下方 v4 / v2
> 段落保留作追溯，凡与之冲突以 v5 报告为准。

- v5 关闭了 GPT v4 终裁的 4 个 T2 live `/replans` blocker（live bulk capture 洗白绕过 / strict 后走
  `hard_minutes` / provenance→LIVE 仅保留可证明的四条 label + 证明表 / 严格同环境零回归证明）。
- **严格同环境（两侧均 `DEEPSEEK_API_KEY=` `CITYNEXUS_AI_API_KEY=`）**：基线 `c6f9024` = `2 failed
  (aiv3_02, v18_3) / 756 passed`（另 v9 collection `FileNotFoundError` 系 git-worktree 复制产物缺文件，非代码）；
  patched HEAD = `2 failed (同 aiv3_02, v18_3) / 817 passed / 15 skipped`。**NEW-vs-baseline = ∅**。
  raw：`raw_full_backend_v5_baseline_SANITIZED.log` / `raw_full_backend_v5_patched.log`；集合 `fail_v5_*.txt`。
- 真 `POST /replans` 级新回归 `test_qoder_live_replans_endpoint.py` L1/L2/L3/L4（fake live 失败指定腿、
  mock 仍显式）——**非空过**：移除 blocker-1 修复后 4/5 失败、控制用例仍过。
- v13（与 v12 同 `v12:{jid}:*` 权威旅程）、v6（离线 real-city REPLAY 旅程）此前被 T2 allowlist（v3 起）
  打断、只在带 key 基线里被 DeepSeek 噪声掩盖；现按批准方式让其 test-local 声明真实路线腿
  （explicit deterministic fixture，非真实 mobility），二者转绿；表外腿仍 synthetic/unavailable（B1 不被动）。
- 前端未受本轮影响：typecheck 覆盖 5 文件 0 新增错误、`vite build` 通过、rendered Playwright 9 passed。

---

# TEST_RESULTS — v4（Xiaomi Truth Hardening，权威版）

> **v4 authoritative (2026-09-19)。** 下文 §1–§6 是 v2 历史细节，保留作追溯；凡与
> 本节冲突者以本节为准。特别地：v2 里"未标记(None)/遗留密封事实保持信任"的措辞
> **已被 v4 的真 allowlist 作废**——`hard_minutes` 只接受
> `EXPLICIT_FROZEN_FIXTURE`/`LIVE_PROVIDER_CAPTURE`，`SYNTHETIC_DEFAULT/None/未知/legacy
> 无来源` 一律 fail-closed。

## V4 结果摘要

提交链：`c6f9024`(基线) → v1 `2cfa1fe` → v2 → v3 → v4 `c1f94d3,656baa5,d306e01,d8b48db(#1),7bf1845(#2),5392c71(#4),cd84897(#5+回归)`。

**全量后端（清 `DEEPSEEK_API_KEY` 跑）**：`4 failed, 810 passed, 15 skipped`。
- NEW-vs-基线 = **∅**（零新增回归）；基线里 **7 条现在转绿**（guardian_v4 ×3、v5、v7、v8、v15）。
- 残留 4 条均基线既有、非真值契约相关：`test_aiv3_02`、`test_v13_integrity`、`test_v18_3_convergence`、`test_v6_predictive_real_city`。
- 原始日志 `raw_full_backend_v4.log`；集合 `fail_baseline.txt` / `fail_v4.txt`。
- **环境注**：测试进程里存在真实 `DEEPSEEK_API_KEY` 时，`test_v16_integration`（`skipif(settings.ai_api_key)` 裸串 SyntaxError）与 `test_v14_grounded_adaptive_recovery`（真调 DeepSeek→502）会失败，**与本 diff 无关**；置空键后二者通过。

**前端**：
- `npm run typecheck`（tsconfig.check 含 V8Experience/LiveRecovery/LocaleContext/budgetEvidence/disruptionState）：**Qoder 新增错误 = 0**。证据 `raw_frontend_typecheck_v4.log` vs `raw_frontend_typecheck_v4_BASELINE.log`：V8Experience 的 3 条错误在基线同现（`group`/`Promise<void>`/`WalletSnapshot`，仅因我插入行整体下移 +4，且均在我 diff 行块之外），LiveRecovery/LocaleContext/budgetEvidence 两侧皆 0。
- `npm run build`：通过（`raw_frontend_build_v4.log`）。
- rendered Playwright：`9 passed`（`raw_frontend_rendered_v4.log`）——含 T3 Today unrelated-accepted（#8）与 T4 修正后的 unverifiedCount 文案（#7）。

**v4 focused 回归清单**：
- `test_qoder_mobility_truth_contract.py`：`test_sealed_legacy_synthetic_fixture_without_quality_fails_closed`（#1 round-trip 去洗白）、`test_explicit_fact_quality_survives_round_trip`（#1）、`test_resolve_fact_quality_is_fail_closed`（#2/B 负向）。
- `test_qoder_live_hard_fallback.py`：live 配置下硬捕获不回落 mock（#4，正反两向）。
- `test_qoder_module_mobility_subsets.py`：每模块 subset 最简 + 未声明腿仍 SYNTHETIC_DEFAULT（#5 sentinel，8 例）。
- `test_qoder_mobility_replan_endpoint.py`：真实 `POST /replans` 的 MOBILITY_DATA_UNAVAILABLE fail-closed 证明（A 约束：v12 保持正向、由端点测承担失败证明）。

**helper per-module 映射**：见 §下方表与 `QODER_V4_IMPLEMENTATION_REPORT.md` §5 表（每模块仅 seed 其 replan 真实触及的 ≤3 条腿；v12 去 module-wide autouse、自 seed 11+1 条 explicit fixture 腿）。

---

# TEST_RESULTS — v2（Xiaomi Truth Hardening，B1–B4 闭合）

基线 commit `c6f9024`；v1 实现 commit `2cfa1fe`；本轮在其上叠加未提交的 v2 改动。

## 1. 四个契约的专项回归（全绿）

| 层 | 用例 | 结果 |
|---|---|---|
| T1 物理身份 (unit) | `tests/test_qoder_physical_identity_contract.py` | 20 passed（含 4 条 v2 新回归：跨 provider 同实体→AMBIGUOUS、node/way 仍 DIFFERENT、任意大写前缀不作 wrapper、跨 provider alias 排除）|
| T2 出行真相 (unit) | `tests/test_qoder_mobility_truth_contract.py` | 13 passed（含 fact_quality 标记 + hard_minutes 门控 + legacy None 兼容）|
| **T2 真实路径 (API/service integration)** | `tests/test_qoder_mobility_replan_endpoint.py` | 2 passed |
| T3 ACK (unit) | `e2e/qoder-ack-resolution.spec.ts` | passed（含死条件可达性断言；渲染级见下）|
| T4 预算 (unit) | `e2e/qoder-budget-evidence.spec.ts` | 2 passed（含 B4 hotel/booking→PARTIAL、statusless→非FULL）|
| **T3 ACK (rendered integration)** | `e2e/qoder-ack-rendered.spec.ts` | 3 passed（真渲染 `/v8/live`，mock experience/replans 取数，断言 DOM）|
| **T4 预算 (rendered integration)** | `e2e/qoder-budget-rendered.spec.ts` | 3 passed（真渲染 `/v8/studio` 的 `studio-feasibility`，断言口径文案）|
| 前端编译门 | `npm run build`（vite，含 TS）| 通过 |

> 测试层标签按 docs/TEST_AND_EVIDENCE_GATE.md 如实标注：`page.evaluate(import 纯函数)` 一律记为 **unit**，不再谎称 E2E。

## 2. T2 真实 replan 路径（B1）——GPT 指出最大缺口，本轮闭合

v1 只测了 `MockMobilityProvider(strict=True)` 原语，没碰真实 `generate_replan`。GPT 指出：replan 会先用**非 strict** 的 bulk capture 把候选腿的 `default_minutes=20` 冻进快照，`_replan_estimate` 再读到 20，strict 分支根本不执行（"后门装了锁，正门敞着"）。

v2 修法：给每条冻结事实打 `fact_quality`（`EXPLICIT_FROZEN_FIXTURE` / `LIVE_PROVIDER_CAPTURE` / `SYNTHETIC_DEFAULT`），并新增 `MobilitySnapshot.hard_minutes()`——它**只拒绝明确标记为 `SYNTHETIC_DEFAULT` 的腿**（未标记的遗留/密封事实保持信任，避免误伤 sealed replay）。replan 的 `_replan_estimate` 改走 `hard_minutes`。

端点级证据（`test_qoder_mobility_replan_endpoint.py`，真实 `POST /replans`）：
- **对照**：fixture 完整时同一 closure 返回 **201**（证明端点能出方案、测试有意义、非空过）。
- **strip 全部候选腿显式事实后**：返回 **422 `MOBILITY_DATA_UNAVAILABLE`**，而非拿假 20 生成方案。
- **候选级**：只 strip design-library、保留 city-park 显式腿时，city-park 候选仍产出（一个候选缺证据不拖垮整体）。

## 3. B1 暴露的既有 replan 测试债——按技术负责人决定处理

正确闭合 B1 后，12 个既有 replan 测试（solver_runtime_gate ort03/06/08/20、solver_v2_integration、post_goal_five_defects f3、vertical_slice_hardening f3×2、wp06_followup_assist、wp06_postgate、v12_autonomous_recovery、guardian_model_evidence、以及 golden 的 F3 族）开始返回 `MOBILITY_DATA_UNAVAILABLE`——它们原先把"用假 20 也能出方案"当预期。

处理（负责人选"改这些旧测试、最符合 GPT"）：新增测试侧 helper `tests/_qoder_explicit_demo_mobility.py`，给 demo 地点图注入**显式** mobility 事实（setdefault，不覆盖真实显式项，不动产品数据 `data/mock/mobility_matrix.json`），以 autouse fixture 精确接到这些测试模块。这些测试从此测的是**可信事实下的** gate/solver/window/budget 行为。

## 4. 全量后端 v2 + 归因（raw log：`raw_full_backend_v2.log`）

- **v2 含改动**：`11 failed, 784 passed, 16 skipped, 1 error`
- **基线**：`12 failed, 748 passed, 16 skipped, 1 error`
- 失败集合差集：
  - v2 新增回归 = v2失败 − 基线失败 = **∅**
  - 基线失败被 v2 修复 = **test_guardian_never_replaces_a_mission_protected_activity**（T1 身份收紧带来）
- 784 = 748 + 25（v2 新增通过）+ 11（旧测试经 helper 转绿）− …；数字与"零新回归 + 修 1 + helper 让既有可过"自洽。

### 4.1 11 个残留失败的性质（原始清单 `fail_v2.txt`）

全部 ⊆ 基线 12（去掉被修复的那条）。症状：`plans/generate` 非 201、`assert 'PROPOSAL_PRESENTED' == 'EXECUTED'`、DeepSeek fallback 断言等——属本副本 synthetic-fixture / 共享 SQLite / 外部 LLM 依赖环境。

### 4.2 flaky 外部依赖证据（回应"别口头归因为环境"）

`test_v14_weather_recovery_freezes_incident_evidence_and_child_plan` 时而 502（`DeepSeek discovery failed`）。已做版本无关性实验：**stash 全部 v2 改动回到 v1 后，同一测试连跑 3 次 = 2 通过 1 失败**，证明该失败是 DeepSeek egress 抖动、**与 v2 代码无关**（traceback 保留在本文件与 raw log）。

### 4.3 collection error（副本产物）

`test_v16_legacy_command...` → `FileNotFoundError: PACKAGE-MANIFEST.json`（基线同样报，复制产物缺文件，非代码缺陷）。

## 5. 渲染级已补，仍如实标注两处边界

- **已交付**：`e2e/qoder-ack-rendered.spec.ts`（3）与 `e2e/qoder-budget-rendered.spec.ts`（3）真渲染
  `/v8/live`、`/v8/studio`，经 `page.route` mock 组件实际 fetch 的 API 后断言 DOM（非 `page.evaluate` 纯函数）。
- **T4 边界（不夸大）**：渲染测试证明的是"活动有价、住宿/交通未知时 `studio-feasibility` 拒绝给出整程已验证结论"这一 **activities 数据边界** 行为；把 hotel 作为独立于 activities 的**第二证据源做跨源聚合**（`tripBudgetEvidence`/`budgetClaimScope`）由 **unit** 层覆盖，因为 `Studio` 组件本身只对 plan.activities 求覆盖。
- **原始日志**：本包含 v2 全量 `raw_full_backend_v2.log`；**基线全量原始日志**将在下一版随包附上（此处基线数字取自上一轮同环境实测）。

## 6. 合并门（HANDOFF v2）

| # | 门槛 | 判定 |
|---|---|---|
| B1 | 真实 replan 路径消灭假 20 | ✅ 端点 422 证据 |
| B2 | 跨 provider 换皮不再被当不同/不被推荐回来 | ✅ T1 三态+排除 |
| B3 | ACK-only 仍 actionable、死条件去除 | ✅ code（渲染待回填）|
| B4 | activity-only 不冒充整程预算验证 | ✅ 聚合器+口径降级+hotel 测试 |
| 零回归 | v2 失败 ⊆ 基线 | ✅ |

最终 v2 裁决：见 QODER_IMPLEMENTATION_REPORT.md 末尾。
