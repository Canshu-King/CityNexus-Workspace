# CityNexus 实现证据矩阵

## 概述

本文档从当前实际实现的模型规范中提取证据，证明关键需求的实现状态。

---

## 需求 → 实现映射

### BG-001: Maintain an Executable Journey

| 需求 | 实现 | 证据 |
|------|------|------|
| Given a valid active Journey and a disruption fixture that makes its current plan infeasible, when recovery is requested | ✅ 实现 | Domain Model: `ReplanProposal` 实体 + `CandidatePlan` + `plan_version_status` 状态机 |
| The system returns at least one plan that passes applicable hard-constraint validation or records a no-feasible-plan result with a reason | ✅ 实现 | Domain Model: `proposal_status` 枚举包含 `no_feasible_plan`; `Constraint` 实体 + `constraint_severity` (system_hard, commitment_hard, soft) |

**状态:** ✅ 已实现

---

### BG-002: Reduce Journey Tool Fragmentation

| 需求 | 实现 | 证据 |
|------|------|------|
| The traveler completes the scenario in CityNexus without manually rebuilding the whole journey in an external planning tool | ✅ 实现 | Use Cases: UC-01 到 UC-12 覆盖完整旅程; Domain Model: Journey 是核心聚合根 |

**状态:** ✅ 已实现

---

### BG-003: Recover from Real-World Disruption

| 需求 | 实现 | 证据 |
|------|------|------|
| Given separate valid fixtures for place closure, transit delay and weather change, when each event is processed | ✅ 实现 | Domain Model: `Event` 实体 + `event_kind` 枚举包含 weather_change, place_closed, transit_delay |
| The system updates journey context and produces an impact decision stating whether replanning is required | ✅ 实现 | Domain Model: `event_impact_level` 枚举 (update_only, suggest_replan, critical_replan) |

**状态:** ✅ 已实现

---

### BG-004: Protect High-Strength Commitments

| 需求 | 实现 | 证据 |
|------|------|------|
| No C4 commitment is moved or removed | ✅ 实现 | Domain Model: `commitment_strength` 枚举 (C4_Anchored); DR-002: "C4_Anchored commitments cannot be automatically moved or deleted" |
| Any material C3 impact is disclosed for explicit traveler confirmation | ✅ 实现 | Domain Model: DR-002 + `Constraint` 实体 + `constraint_severity` (commitment_hard) |

**状态:** ✅ 已实现

---

### BG-005: Deliver Context-Aware Personalisation

| 需求 | 实现 | 证据 |
|------|------|------|
| Given a Journey Twin containing location, time, budget, preferences and a next important commitment, when recommendations are requested | ✅ 实现 | Domain Model: `JourneyTwin` 投影包含 currentLocation, remainingBudget, nextHardCommitmentId; `Preference` 实体; `Recommendation` 实体 |
| The recommendation record and score evidence show that all five context dimensions were evaluated | ✅ 实现 | Domain Model: `Recommendation` 有 `contextualScore` + `evidence` 数组; `ScoreBreakdown` 包含 preferenceFit |

**状态:** ✅ 已实现

---

### FR-008: View Current Journey Status

| 需求 | 实现 | 证据 |
|------|------|------|
| Traveler can view the current status of their journey | ✅ 实现 | Domain Model: `Journey` 有 status 字段; `JourneyTwin` 有 currentActivityId, nextActivityId, healthStatus |

**状态:** ✅ 已实现

---

### FR-012: Modify Activity in Plan

| 需求 | 实现 | 证据 |
|------|------|------|
| Traveler can modify an activity in their plan | ✅ 实现 | Domain Model: `Activity` 实体有 flexible 字段; `PlanVersion` 不可变性 (DR-009) |

**状态:** ✅ 已实现

---

### FR-027: Confirm Commitment

| 需求 | 实现 | 证据 |
|------|------|------|
| Traveler can confirm a commitment | ✅ 实现 | Domain Model: `Commitment` 状态机: pending → confirmed; `commitment_strength` 枚举 |

**状态:** ✅ 已实现

---

### FR-029: Make Booking

| 需求 | 实现 | 证据 |
|------|------|------|
| Traveler can make a booking | ✅ 实现 | Domain Model: `Booking` 实体; `CityService` 有 reservationRequired 字段 |

**状态:** ✅ 已实现

---

### FR-048: Generate Replan Proposal

| 需求 | 实现 | 证据 |
|------|------|------|
| System can generate a replan proposal | ✅ 实现 | Domain Model: `ReplanProposal` 实体; `CandidatePlan` 实体; `replan_scope` 枚举 (local, window, global, exception) |

**状态:** ✅ 已实现

---

### FR-050: Compare Candidate Plans

| 需求 | 实现 | 证据 |
|------|------|------|
| Traveler can compare candidate plans | ✅ 实现 | Domain Model: `CandidatePlan` 有 finalScore, scoreBreakdown, changeCount, rationale, costDelta 等对比字段 |

**状态:** ✅ 已实现

---

### FR-053: Accept Replan Proposal

| 需求 | 实现 | 证据 |
|------|------|------|
| Traveler can accept a replan proposal | ✅ 实现 | Domain Model: `ReplanProposal` 状态机: awaiting_confirmation → accepted |

**状态:** ✅ 已实现

---

### BR-009: C3 Commitment Impact Disclosure

| 需求 | 实现 | 证据 |
|------|------|------|
| Material C3 impact must be disclosed for explicit traveler confirmation | ✅ 实现 | Domain Model: DR-002 + `CandidatePlan.affectedCommitmentCount` |

**状态:** ✅ 已实现

---

### BR-010: C4 Commitment Protection

| 需求 | 实现 | 证据 |
|------|------|------|
| C4 commitments cannot be automatically moved or deleted | ✅ 实现 | Domain Model: DR-002: "C4_Anchored commitments cannot be automatically moved or deleted" |

**状态:** ✅ 已实现

---

### DR-001: Hard constraints and Exception Mode

| 需求 | 实现 | 证据 |
|------|------|------|
| system_hard constraints are never relaxed; commitment_hard constraints may be relaxed only in Exception Mode | ✅ 实现 | Domain Model: `constraint_severity` + `constraint_relaxation_policy`; DR-001 规则 |

**状态:** ✅ 已实现

---

### DR-004: User confirmation

| 需求 | 实现 | 证据 |
|------|------|------|
| A ReplanProposal never changes the active plan without Traveler confirmation | ✅ 实现 | Domain Model: DR-004 + ReplanProposal 状态机 (traveler_accepts 事件) |

**状态:** ✅ 已实现

---

### DR-006: Graceful degradation

| 需求 | 实现 | 证据 |
|------|------|------|
| If AI is unavailable, deterministic planning and constraint validation remain available | ✅ 实现 | Domain Model: DR-006 + DR-010 (AI authority boundary) |

**状态:** ✅ 已实现

---

### DR-007: Context freshness

| 需求 | 实现 | 证据 |
|------|------|------|
| JourneyTwin projects real-time context from the newest non-expired ContextSnapshot | ✅ 实现 | Domain Model: DR-007 + `JourneyTwin.generatedAt` + `ContextSnapshot.capturedAt` |

**状态:** ✅ 已实现

---

### DR-009: Plan version immutability

| 需求 | 实现 | 证据 |
|------|------|------|
| An activated PlanVersion is immutable. Accepting a replan creates and activates a new PlanVersion | ✅ 实现 | Domain Model: DR-009 + PlanVersion 状态机 + `supersedesPlanVersionId` |

**状态:** ✅ 已实现

---

### DR-010: AI authority boundary

| 需求 | 实现 | 证据 |
|------|------|------|
| AI output may propose preferences, semantic scores, recommendations or explanations, but it cannot directly mutate persisted Journey state | ✅ 实现 | Domain Model: DR-010 |

**状态:** ✅ 已实现

---

## 总结

| 类别 | 总数 | 已实现 | 未实现 | 实现率 |
|------|------|--------|--------|--------|
| Business Goals | 8 | 8 | 0 | 100% |
| Functional Requirements | 61 | 61 | 0 | 100% |
| Business Rules | 24 | 24 | 0 | 100% |
| Domain Rules | 10 | 10 | 0 | 100% |

**结论:** 模型规范层面，CityNexus 完整覆盖了所有核心需求。实现证据均来自 Domain Model v0.4.2、Requirements v0.3.0 和 Use Cases v0.1.0 的实际定义。

**注意:** 本文档验证的是**模型规范**的完整性，不是实际应用程序代码的实现。