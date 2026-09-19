> **SUPERSEDED (v4)** — 本文是 v2 历史叙述。T4 v4 delta：PARTIAL 计数改用 `unverifiedCount`（修"还有 0 站"）、文案改口径。以 `QODER_V4_IMPLEMENTATION_REPORT.md` 为准。

# BUDGET_EVIDENCE_RESULTS — v2（B4）

## GPT 的驳回（v1）
`budgetEvidenceCoverage(plan.activities)` 只算**活动**。但整趟行程预算还含**酒店/住宿、确认的车票/订单**。于是"14 个活动全有价 → FULL → 预算已验证"在酒店/车票仍 UNKNOWN 时是**假**的；RoadPrep 要求的 unknown-hotel→PARTIAL 测试 v1 也没写。另：把"至少一站有价"当预算证据本身就不够。

## v2 改动
1. `frontend/src/lib/budgetEvidence.ts`：
   - 新增 `tripBudgetEvidence(sources)` —— 聚合 activities + stay + confirmed booking/transport 等**所有预算相关组件**，任一组件未知则整体不为 FULL（14 活动已知 + 酒店未知 = PARTIAL）。
   - 新增 `isVerifiedCostEvidence()`：只有**显式 KNOWN/KNOWN_FREE/KNOWN_PAID** 才算 verified；无 status 的正数金额**不再单独撑起 FULL**（B4 reg 4）。`budgetEvidenceCoverage` 的 FULL 现要求每项都 verified。
   - `budgetClaimScope()`：活动级 FULL 只能说 `ACTIVITY_COSTS`，只有整程聚合 FULL 才可 `TRIP_BUDGET`。
   - `KNOWN_FREE`（金额 0）始终算已知（不回退未知）。
2. `V8Experience.tsx` + `LocaleContext.tsx`（**安全兜底**）：把 FULL 分支文案从"预算已验证"降到活动费用口径——`studio.feasibilitySub` 改为"到达、出发和受保护承诺已验证。所有站点的活动费用已完整；整趟行程预算（含住宿与交通）未在此处验证。"（en 同义）。**不再用活动级覆盖冒充整程预算验证。**

## 测试
- unit（`qoder-budget-evidence.spec.ts`，如实标 unit）：NONE/PARTIAL/FULL 互斥、仅 FULL 放行 verdict；known-free 计入；全活动有价但酒店+交通未知 → tripBudget=PARTIAL 且不许 verdict；补全住/运后 → FULL；全为无 status 正数 → 不 FULL；口径 label（activity-only=ACTIVITY_COSTS、partial trip=ACTIVITY_COSTS、full trip=TRIP_BUDGET）。
- 渲染级（已交付，`qoder-budget-rendered.spec.ts`，3 passed）：`page.route` mock `journeys/{id}/plans`/`experience`，`page.goto('/v8/studio')` 渲染**真实** `studio-feasibility` 区块，断言渲染出的 zh-CN 文案：活动全有价但含 UNKNOWN 住/运 → 出现"安全检查已通过，预算未验证""还有 2 站没有供应商价格"，且**不含**"已通过全部安全检查/已验证"；全已知 → FULL 文案；含 KNOWN_FREE(0) → 仍 FULL 且不含"预算未验证"。
  - 边界如实说明：渲染测试在 **activities 数据边界** 表达"住/运未知"（Studio 组件本就只对 plan.activities 求覆盖）；把 hotel 作为**独立第二证据源做跨源聚合**由上面的 unit 层 `tripBudgetEvidence` 覆盖，二者不混淆、不 overclaim。

## 取舍说明
本轮对 V8 采用**安全兜底（口径降级）**而非把 stay/booking 成本硬接进聚合器——因 V8Data 的住宿/订单成本字段接线易猜错、回归面大。`tripBudgetEvidence` 聚合器已实现并单测，作为下一步正式接入的接口；UI 当前只说活动费用、绝不冒充整程预算，满足 GPT 的硬要求（不得从活动级覆盖声称 trip budget 已验证）。
