> **SUPERSEDED BY QODER_V4_IMPLEMENTATION_REPORT.md** — v3 报告，历史保留。当前权威结论见 `QODER_V4_IMPLEMENTATION_REPORT.md` + `TEST_RESULTS.md`；v4 已闭 T2 洗白（#1/#2/#4）、#5 per-module、typecheck 覆盖、T4 计数、Today rendered。

# QODER_V3_IMPLEMENTATION_REPORT — Xiaomi Truth Hardening v3

针对 GPT 对 v2 的独立复审（裁决 `QODER_V2_NOT_READY_FOR_INTEGRATION`，附 v3 RoadPrep 11 项必修）。
基线 `c6f9024`；v1 `2cfa1fe`；v2 `1b8fe42`；v3 commits `f971771`/`ce152df`/`c47bc1f`。全程隔离副本，未动主树。

## 逐条落实 GPT 的 v3 必修
1. **T2 真 allowlist**（V3-1）：`hard_minutes` 只接受 `HARD_FEASIBLE_QUALITIES = {EXPLICIT_FROZEN_FIXTURE, LIVE_PROVIDER_CAPTURE}`；`SYNTHETIC_DEFAULT / None / 未知` 一律拒（fail closed）。不再"定义 allowlist 却用 denylist"。
2. **None/legacy 不再盲信**（V3-1）：`from_minutes` 默认打 `EXPLICIT_FROZEN_FIXTURE`（调用方显式分钟表，非兜底）；`from_evidence` 按**已存 provenance** 诚实推导——密封的 `SYNTHETIC_FIXTURE` 是矩阵真实腿→EXPLICIT，无 provenance→None→拒。blanket runtime default 只在现场 replan 捕获处被打 `SYNTHETIC_DEFAULT` 并拒。回归 `test_hard_minutes_fails_closed_on_unrecorded_quality`。
3. **候选级 endpoint 确定性证明**（V3-2）：candidate A 腿显式、仅 strip B 腿→**必须 201 且 proposal 含 A、不含 B**（不再"422 也算过"）。
4. **旧测试 helper 收窄**（V3-3）：删去"全图 + 统一 15 + 模块 autouse"，改 `seed_explicit_mobility(monkeypatch, {pairs})` 手声明路线表（真实邻接、各异时长）；未列 pair 仍缺。加 **sentinel** `test_v3_03_seed_helper_neutralises_b1_sentinel`：seeded 腿 EXPLICIT 可用、未列腿仍 SYNTHETIC_DEFAULT 不可用 → helper 没中和 B1。
5. **T1 跨 provider 近距漂移**（V3-4）：`_near_coordinates` 真实地理近似距离阈值 ~60m；同名+类别兼容+近距→AMBIGUOUS（非 DIFFERENT，也非 SAME）。回归含 ~10m→AMBIGUOUS、2km/500m→DIFFERENT。
6. **渲染级 /v8/today**（V3-5）：ack-rendered spec 增 Today 两例（`today-attention` 在 ACK-only 显示"1 项变化"、linked accepted 清除），与 Live 同规则。
7. **修重复 TS 类型 + typecheck 门**（V3-6）：删 `budgetEvidence.ts` 重复 `BudgetEvidenceCoverage`；新增 `npm run typecheck`（`tsc --noEmit`，覆盖真相 lib 模块）。**typecheck + build 双绿。**
8. **标题范围诚实**（V3-7）：Studio `feasibilityPassed` 由"已通过全部安全检查"→"行程约束检查已通过"、partial→"行程约束检查通过，费用证据不完整"（en 同），不再与"整程预算未验证"自相矛盾。
9. **未知 replan 错误不外泄**（V3-7b）：`humanReplanReason` 未映射码返回通用安全文案，raw 只进 Advanced。
10. **原始日志齐备**（V3-8）：随包附 `raw_full_backend_baseline.log`（c6f9024 worktree 实测）、`raw_full_backend_v3.log`、frontend typecheck/build/rendered 原始输出、`fail_baseline.txt` / `fail_v3.txt`。

## T4 范围（遵 GPT 刻意限制）
**不**把 stay/booking 接进 Studio（GPT 明确 v3 不要求，避免收口轮又变产品轮）。`tripBudgetEvidence` 跨源聚合保留为 unit 层未来接口；UI 只声明活动费用范围。

## 验证
- 后端 v3 全量：`9 failed / 790 passed / 16 skipped / 1 error`。
- **归因（含真实 baseline raw log）**：v3 失败集 ⊆ baseline(c6f9024 worktree) 失败集，**零新回归**；v3 另把 `guardian_over_mission`、`v8_stay_mobility` 转绿。
- 前端：`npm run typecheck` 0、`npm run build` 0、qoder spec **11 passed**（ack unit+Live+Today、budget unit+rendered）。
- 专项：T1 23 / T2 unit 13 / T2 端点 3（含 sentinel）全绿。

## 最终 v3 裁决
`QODER_V3_PATCH_READY_FOR_INTEGRATION`

GPT v3 全部 11 项均已落实并有对应测试/原始日志支撑；T4 按 GPT 指示停在安全降级；主仓 baseline 冻结与真实 routing provider 是**下一整合阶段**、需负责人批准，不在本轮 patch 范围。是否合并由 GPT 独立复审 + 负责人决定，Qoder 不合 main。
