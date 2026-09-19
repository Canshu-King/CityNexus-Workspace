# MOBILITY_TRUTH_RESULTS — v2（B1）

> **v4 更新（以此为准）**：`hard_minutes` 现为**真 allowlist**——只接受 `EXPLICIT_FROZEN_FIXTURE` / `LIVE_PROVIDER_CAPTURE`；`SYNTHETIC_DEFAULT / None / 未知 / legacy 无来源` 一律 fail-closed（v4 #1）。`from_minutes` 默认 unknown provenance，显式矩阵由调用方声明（v4 #3）。下文若有"None/legacy 保持信任"的 v2/v3 措辞，均以此为准作废。

## GPT 的驳回（v1 不足）
v1 只在 `_replan_estimate` 的 **fallback** 用了 `require_explicit_facts=True`。但真实 `generate_replan` 先构一大坨 `mobility_pairs`（含替换候选 inbound/outbound），用**非 strict** 的 `capture_runtime_mobility_snapshot` 冻结 → 缺显式事实的腿先落成 `default_minutes=20` 进快照 → `_replan_estimate` 里 `mobility.estimate_minutes` 直接读到 20，strict 分支永不触发。且 v1 那 9 个测试全没打 `/replans`/`generate_replan`。

## v2 设计（真值门 + 候选级）
1. **事实质量分级**（`provider_snapshots.TravelEstimateFact.fact_quality`，经 evidence 往返保留）：
   `EXPLICIT_FROZEN_FIXTURE` / `LIVE_PROVIDER_CAPTURE` / `SYNTHETIC_DEFAULT`。
   `MockMobilityProvider.fact_quality(o,d)` 判某 pair 在不在显式矩阵；`capture_mobility_snapshot` 在**每个分支**（主/回退）解析 `active_provider` 并落质量标。
2. **真值门 `MobilitySnapshot.hard_minutes()`（v4 真值，以此为准）**：真 allowlist——只接受 `EXPLICIT_FROZEN_FIXTURE` / `LIVE_PROVIDER_CAPTURE`；`SYNTHETIC_DEFAULT`、缺失、`None`、未知或 legacy 无来源一律 fail-closed 抛 `KeyError`（v3 "未标记(None) 保持信任"的措辞已作废，见顶部 v4 banner）。
3. **来源解析与封存（v4 #1/#2/#4）**：`_resolve_fact_quality` 完全 fail-closed——只认 provider 自报的 `fact_quality`，分类异常或 provider 不声明即 UNKNOWN，且**删除按 provider-key 猜测**；`_derive_fact_quality_from_provenance` 不再把 `SYNTHETIC_FIXTURE` 洗成 `EXPLICIT`；`authoritative_v12` 在封存与恢复 evidence 两处持久化真实 `fact_quality`。live 已配置时硬捕获不再回落 mock fixture（#4）。
4. **replan 走真值门**：`_replan_estimate` 首读改 `hard_minutes`（`estimate_minutes` 仍供 demo/geometry 用）。于是正门冻进来的假 20 在消费点被拒 → 落回 strict on-demand capture → `MobilityDataUnavailable` → 422 `MOBILITY_DATA_UNAVAILABLE`，且**逐候选**（一个缺证据不拖垮其它）。
5. **初始化先于首用**：把 `created/failed_reasons/mobility_unavailable_pairs` 上移到首个候选循环之前，消除 v1 遗留的 `UnboundLocalError`（GPT B1 gate point 4）。

## 端点级证据（unit 之外新增 API/service integration）
`tests/test_qoder_mobility_replan_endpoint.py`，真实 `POST /api/v1/journeys/{id}/replans`：
- 对照（fixture 完整）→ 201；证明该 closure 本来可恢复，失败只因证据缺失。
- 把候选腿显式事实全部 strip（退 default）→ **422 `MOBILITY_DATA_UNAVAILABLE`**（绝不用假 20 判可行/绝不误报"无替代"）。
- 只 strip design-library、保留 city-park 显式腿 → city-park 候选仍产出（候选级、非 all-or-nothing）。

## 既有测试债
12 个原本依赖假 20 的 replan 测试改由 helper 注入 demo **显式** mobility（见 TEST_RESULTS §3），不改产品数据。

## 单元（`test_qoder_mobility_truth_contract.py`，13）
显式腿保留其分钟；缺腿 strict 抛错；非 strict capture 仍返回 20 但**标为 SYNTHETIC_DEFAULT**；`hard_minutes` 拒 default/None/未知腿、只信任显式或 live 腿（真 allowlist，fail-closed）；`fact_quality` 分类正确。端点测试与 v12 场景各自显式声明其真实腿来源，不再依赖洗白。

范围：本轮仍未部署 Valhalla、未用几何估算冒充真值。
