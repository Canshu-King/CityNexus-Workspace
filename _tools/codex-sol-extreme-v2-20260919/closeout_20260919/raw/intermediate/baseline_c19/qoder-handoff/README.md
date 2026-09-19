# CityNexus — Qoder Xiaomi Truth Hardening 交接包（v6, 2026-09-19）

隔离实现/证明线针对 GPT 的 `QODER_V5_BLOCKED` 终裁（live `/replans` 修复已接受，仅剩一个窄的 legacy provenance 推断洗白）做 v6 收口。
全程在隔离副本 `D:\moodle\_qoder_th_20260918`，**未碰主仓/git init/merge/Valhalla/Frontend vNext/新功能；未重开 T1/T3/T4；未动测试 helper**。

## 先读这两份（v6 权威）
1. `QODER_V6_IMPLEMENTATION_REPORT.md` — v6：legacy provenance 推断改 exact + fail-closed + producer 侧显式 quality + targeted 回归 + L1-L4 focused raw log + 同环境零回归。
2. `TEST_RESULTS.md` — 顶部 v6 权威节（v5/v4/v2 保留追溯）。

> v5 及更早报告均已标 `SUPERSEDED BY QODER_V6_IMPLEMENTATION_REPORT.md`。

## 基线
self-git 合成基线 `c6f9024`（v1–v5 历史提交保留在 patch 里）。提交链见 `QODER_V6_IMPLEMENTATION_REPORT.md`。

## 关键补丁
- `qoder_xiaomi_truth_hardening_v6.patch` — 相对 `c6f9024` 的完整 diff（app+tests+frontend）。
- `..._v6_app.patch` / `..._v6_tests.patch` — 产品改动 / 测试改动 分块，便于分别复核。
- `CHANGED_FILES.txt` — 变更文件清单。

## 覆盖了什么（v5 四个 live blocker + v6 一个 provenance blocker）
- **blocker 1（硬）**：live `/replans` bulk capture 绕过——live 配好时把 mock fallback 腿降级为非硬，真实 Valhalla
  失败的腿不再靠 mock 显式矩阵洗进 hard truth；候选级隔离。真 `POST /replans` L1/L2/L3/L4 测试证明，**非空过**
  （拆掉修复 4/5 失败）。
- **blocker 2**：strict 重捕后走 `hard_minutes()`（单一硬门入口）。
- **blocker 3（v6 收口）**：`_derive_fact_quality_from_provenance` 改 exact + fail-closed——删掉所有宽匹配
  （`"LIVE" in prov` / `startswith("SEALED")` / `CAPTURED_REPLAY`→LIVE / `RUNTIME_CAPTURE`→LIVE）；现仅精确
  `LIVE_CAPTURE` 可升 LIVE，其余历史 label（含 `SEALED_REAL_REPLAY_WITH_EXPLICIT_SYNTHETIC_FALLBACK`、
  `SEALED_REPLAY_OR_SYNTHETIC_FIXTURE_EXPLICIT`、`CAPTURED_REPLAY`、`SEALED_INCIDENT_REPLAY`、`RUNTIME_CAPTURE`）
  无显式 quality 一律 None→hard_minutes fail-closed；producer 侧改为透传真实 quality（非按名猜）。
- **blocker 4**：两侧清 `DEEPSEEK_API_KEY`/`CITYNEXUS_AI_API_KEY` 的严格同环境 baseline vs patched 全量对照。
- 附带：v13、v6 被 T2 allowlist 打断的两个预测恢复测试，按批准方式 test-local 声明真实路线腿（非真实 mobility）转绿。

## 验证（见各 raw log）
- 严格同环境：基线 `2 failed(aiv3_02,v18_3)/756 passed`（+v9 worktree 复制产物 collection 错，非代码）；
  patched `2 failed(同)/817 passed/15 skipped`。NEW-vs-基线 = ∅。
- 前端未受影响：typecheck（5 文件）0 新增错误；`vite build` 通过；rendered Playwright 9 passed。

## 未做（GPT 批准的范围外，属下一阶段整合门）
冻结主仓 authoritative git 基线 → 建 integration branch → 整合 patch → 主仓复跑 truth gates →
配置真实 routing provider → 厦门 mobility smoke → Xiaomi 13 Ultra。

## 状态：已获终裁（2026-09-19）
`QODER_V6_PATCH_READY_FOR_INTEGRATION`。Truth Hardening 隔离实现线（v1→v6）完成，无需 v7。
下一阶段为整合（owner 执行）：冻结主仓 authoritative git 基线 → 建 integration branch → 人工 reconcile
Qoder 累计 patch → 主仓同净化环境复跑 T1–T4/typecheck/build/rendered → 配置真实 routing provider →
厦门真实 mobility smoke → Xiaomi 13 Ultra fresh trial。详见 `QODER_V6_IMPLEMENTATION_REPORT.md` 末节。
