> **SUPERSEDED BY QODER_V4_IMPLEMENTATION_REPORT.md** — v2 顶层报告，历史保留。当前权威结论见 `QODER_V4_IMPLEMENTATION_REPORT.md` + `TEST_RESULTS.md`；下文若与之冲突以 v4 为准。

# QODER_IMPLEMENTATION_REPORT — v2（Xiaomi Truth Hardening）

## 角色与本轮目标
按 GPT 对 v1 的独立复审（裁决 `QODER_PATCH_NOT_READY_TO_MERGE`）做 v2 收口。Qoder 仍为
**隔离实现/证明线**，不动主树、不合 main。基线 `c6f9024`；v1 `2cfa1fe`；v2 实现 `1b8fe42`。

## 逐条回应 GPT 的 v2 指令

| GPT 指令 | v2 落实 | 证据 |
|---|---|---|
| T2 在**真实 replan 路径**消灭假 20，别只测 strict 原语 | 冻结事实打 `fact_quality`，新增 `hard_minutes` 只拒 `SYNTHETIC_DEFAULT`；`_replan_estimate` 走 hard_minutes | 端点 `POST /replans`：对照 201 / strip→**422 MOBILITY_DATA_UNAVAILABLE** / 候选级 |
| 区分 SAME 与 AMBIGUOUS 排除语义 | `is_same_physical_venue`=仅 SAME；新增 `should_exclude_replacement_candidate`=SAME+AMBIGUOUS | T1 unit 20 |
| 覆盖跨 provider 同实体歧义 | 不同 provider 元组 + 同坐标同名 → AMBIGUOUS 并 fail-safe 排除 | v2 回归 test_v2_01/02/04 |
| 修死 ACK-only UI 条件 + 真渲染集成 | 去掉 `openDisruptions===0` 守卫；渲染 `/v8/live` 断言两提示同现 | ack unit + ack-rendered 3 passed |
| 预算覆盖声明真实范围（含 stay/booking） | `tripBudgetEvidence` 聚合 + `isVerifiedCostEvidence`（无 status 正数不撑 FULL）+ 文案降级到活动费用口径 | budget unit + budget-rendered 3 passed |
| 不把未映射的 replan 错误串泄漏到 traveler UI | 仅保留既有 `humanReplanReason` 人话映射；内部 code 在 advanced | v1 已具备，v2 未回退 |
| 附原始测试日志 | 附 `raw_full_backend_v2.log` + `fail_v2.txt`；基线全量日志随下一版 | TEST_RESULTS |
| 建 authoritative git baseline 再整合 | **未做**（动主仓/不可逆，待负责人批准）；见 OPTIONAL_FINDINGS | — |

## 全量归因（关键）
v2 含改动 `11 failed / 784 passed` ⊆ 基线 `12 failed`：**零新增回归**，并额外修复基线里
`test_guardian_never_replaces_a_mission_protected_activity`。残留失败属 synthetic-fixture / 共享
SQLite / 外部 DeepSeek 环境；其中 v14_weather 的 502 已用"回到 v1 连跑 3 次仍随机失败"证明与代码无关。

B1 正确闭合后暴露的 12 个既有 replan 测试，按技术负责人决定改由测试侧 helper 注入 demo **显式**
mobility（不改产品数据），使它们在可信事实下测各自主题。

## 已知边界（不夸大）
- T4 渲染测试在 activities 数据边界复现 B4；跨源 `tripBudgetEvidence` 聚合由 unit 层覆盖（Studio 仅对 plan.activities 求覆盖）。
- 未部署 Valhalla、未做 Frontend vNext、未动时区/幂等、未冻结主仓 baseline。

## 合并/评审说明
patch 为相对 `c6f9024` 的 clean diff（`qoder_xiaomi_truth_hardening_v2.patch`，28 文件）。与 EAC/dsh
在 `main.py`、`mock_replan_engine.py`、`V8Experience.tsx`、`LiveRecovery.tsx`、`providers/runtime/
snapshot_capture` 处可能冲突，需人工合并；helper 依赖 `tests/_qoder_explicit_demo_mobility.py`。

## 最终 v2 裁决
`QODER_V2_PATCH_READY_FOR_INTEGRATION`

理由：GPT v2 六门（B1 真路径、B2 换皮、B3 渲染一致、B4 预算范围、零回归、原始日志）均达成或有
如实标注的边界；仍由 GPT 独立复审后决定是否合并，Qoder 不合 main。
