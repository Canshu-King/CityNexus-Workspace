> **SUPERSEDED (v4)** — 本文是 v2 历史叙述。T3/ACK 在 v3–v4 继续演进（Today/Live 真 rendered、unrelated-accepted 仍显 unresolved、`Set<string>` 类型修正），以 `QODER_V4_IMPLEMENTATION_REPORT.md` + `V4_STATUS.md` 为准。

# ACK_RESOLUTION_RESULTS — v2（B3）

## GPT 的驳回（v1）
1. v1 e2e 只是 `page.evaluate(import('/src/lib/disruptionState.ts'))` 调纯函数 —— 是 unit，不是渲染级，没真渲染 Today/Live。
2. 一个 v1 自己没意识到的**死条件**：`LiveRecovery.tsx` 里
   `acknowledgedOnly.length > 0 && openDisruptions.length === 0`。
   而 `acknowledgedOnly := ACKNOWLEDGED 且 isDisruptionOpen == true`，天然是 `openDisruptions` 的**子集**，
   所以 `acknowledgedOnly>0 && open===0` **恒不成立** → "已知晓，仍待处理"这句 UI 永远不显示。

## v2 改动
1. `frontend/src/features/execution/LiveRecovery.tsx`：去掉那句永不成立的 `openDisruptions.length === 0` 守卫，
   改为 `acknowledgedOnly.length > 0` 即渲染"已知晓，仍待处理"——事件仍 open 时该提示可达。
2. 共享谓词 `lib/disruptionState.ts`（`isDisruptionOpen` / `isDisruptionAcknowledgedOnly`）保留，Today(`V8Experience`) 与 Live 仍共用，保证同事件同状态。

## 测试
- unit（`qoder-ack-resolution.spec.ts`，如实标 unit）：ACK-only 仍 open + 被 flag（显式断言二者同真，坐实死条件已修）；关联 ACCEPTED 才 resolve；RESOLVED/IGNORED/带 resolved_at 关闭；不相关 ACCEPTED 不关闭。
- 渲染级（已交付，`qoder-ack-rendered.spec.ts`，3 passed）：`page.route` mock `journeys/{id}/experience` 与 `/replans`，`page.goto('/v8/live')` 渲染**真实** `V8Experience` shell + `LiveRecovery`，断言 DOM：
  1. ACKNOWLEDGED + 无关联 ACCEPTED → `live-disruption` 与 `live-acknowledged`（"已知晓，仍待处理"）**同时可见**（证明死条件已修、文案可达）；
  2. 关联（trigger_event_id 命中）ACCEPTED → 二者 `toHaveCount(0)`、`live-handled` 可见；
  3. 不相关 ACCEPTED → 事件仍 open（二者仍可见）。
  满足 B3 的渲染级 Today/Live 一致性证明。
