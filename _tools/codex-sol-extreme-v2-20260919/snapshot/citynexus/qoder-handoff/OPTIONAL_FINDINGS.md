# OPTIONAL_FINDINGS & 已知缺口 — v2

## 本轮明确未做（守范围，未 overclaim）
- **B5 · authoritative git baseline**：GPT 要求整合前先把当前 CityNexus 冻结成真正 git 基线。这要写主仓 `.git`、属不可逆且动主树范围，**未做**，待技术负责人批准。在此之前 v2 仍只在隔离副本推进、不并主树。
- **可信 routing provider（live Valhalla）**：GPT 把"真正 Xiaomi 动态重规划试用"的硬门之一定为接真实 routing source 跑厦门实测路线。本轮是 **truth-safe fail-closed 工程冒烟**，未部署 Valhalla。二者区别已在报告里写清。
- **T5 timezone / T6 idempotency**：仍未动（不抢 B1–B4）。
- **证据层缺口**：T3/T4 的"渲染级"集成测试由并行子代理补 `e2e/qoder-ack-rendered.spec.ts` / `qoder-budget-rendered.spec.ts`；本轮 handoff 的 §待回填 以其真实运行结果为准，若未闭合会在报告里如实标注，不冒充覆盖。

## 措辞订正（延续 GPT 意见）
- baseline 的 11/11/11/7 legs 称 **baseline frozen mobility facts**，非"真实 routing 测量"（provider=citynexus-synthetic-fixture）。
- 全量残留失败与 v14_weather 502 归因：本副本 synthetic-fixture / 共享 SQLite / 外部 DeepSeek egress 环境；其中 weather 那条已用"回到 v1 连跑 3 次仍随机失败"证明与 v2 代码无关（见 TEST_RESULTS §4.2）。

## 对 helper 注入显式 mobility 的坦白
为闭合 B1，12 个既有 replan 测试改由测试侧 helper 注入 demo 显式 mobility（不改产品数据）。这不是"绕过 B1"：B1 保护的是"缺证据时不得凭空造 20 判可行"；这些测试的意图是测 solver/gate/window/budget，本就该在**有可信 mobility** 的前提下测。产品默认路径（无显式事实）在 replan 下现在会 fail-closed 到 422，已由端点测试证明。
