# Golden Scenario 证据文档

## 概述

本文档分析 CityNexus 领域模型是否能够支持完整的 Golden Journey Scenario：

> 用户计划天津旅行；有一个已经付款的海河游船；有晚餐预约；白天有普通景点；天气突然变化；某个普通活动需要调整；系统保护游船和晚餐；生成替代方案；用户接受；新计划成为 active；JourneyTwin 和 UI 同步变化。

## Golden Scenario 步骤分析

### 1. Journey 创建 ✓

**模型覆盖：**
- `Journey` 实体存在（identity: journeyId）
- 字段：destinationCity, originPlaceId, finalDestinationPlaceId, startAt, endAt, budgetLimit, status, activePlanVersionId, healthStatus
- 生命周期：draft → planned → active → paused → completed / cancelled

**证据：**
```yaml
entities:
  Journey:
    identity: journeyId
    fields:
      destinationCity: string (required)
      startAt: datetime (required)
      endAt: datetime (required)
      budgetLimit: valueObjectRef[Money] (required)
      status: enumRef[journey_status]
```

**状态：** ✅ 支持

---

### 2. Plan 生成 / PlanVersion ✓

**模型覆盖：**
- `PlanVersion` 实体存在
- 字段：versionNumber, createdAt, planningMode, score, feasibility, status, totalEstimatedCost 等
- 生命周期：draft → candidate → active → superseded / rejected / archived

**证据：**
```yaml
entities:
  PlanVersion:
    identity: planVersionId
    relationships:
    - type: composition
      target: Activity
      role: contains
```

**状态：** ✅ 支持

---

### 3. Activity ✓

**模型覆盖：**
- `Activity` 实体存在
- 字段：title, category, sequence, plannedWindow, flexible, priority, status, travelFromPrevious, estimatedCost, actualCost

**证据：**
```yaml
entities:
  Activity:
    identity: activityId
    fields:
      title: string (required)
      plannedWindow: valueObjectRef[TimeWindow] (required)
      flexible: boolean (required)
      priority: integer (required)
```

**状态：** ✅ 支持

---

### 4. Booking ✓

**模型覆盖：**
- `Booking` 实体存在
- 字段：providerId, providerBookingRef, reservedWindow, status, cancellationDeadline

**证据：**
```yaml
entities:
  Booking:
    identity: bookingId
    fields:
      providerId: string (required)
      providerBookingRef: string (required)
      reservedWindow: valueObjectRef[TimeWindow] (required)
      status: enumRef[booking_status]
```

**状态：** ✅ 支持

---

### 5. Payment ✓

**模型覆盖：**
- `PaymentTransaction` 实体存在
- 字段：amount, provider, status, authorisedAt, capturedAt, createdAt, updatedAt
- 生命周期：initiated → authenticating → authorised → captured → failed / refunded

**证据：**
```yaml
entities:
  PaymentTransaction:
    identity: paymentTransactionId
    invariants:
    - 'exactly_one_payment_subject: booking_xor_order'
    relationships:
    - type: association
      target: Booking
      role: subject_booking
```

**状态：** ✅ 支持

---

### 6. Commitment ✓

**模型覆盖：**
- `Commitment` 实体存在
- 字段：strength (C0-C4), kind, lockedWindow, cancellationCost, status, sourceType, sourceReferenceId
- 生命周期：pending → confirmed → fulfilled / cancelled / broken

**证据：**
```yaml
enums:
  commitment_strength:
  - C0_Flexible
  - C1_Preferred
  - C2_Reserved
  - C3_Guaranteed
  - C4_Anchored

entities:
  Commitment:
    identity: commitmentId
    fields:
      strength: enumRef[commitment_strength]
      lockedWindow: valueObjectRef[TimeWindow]
      cancellationCost: valueObjectRef[Money]
```

**状态：** ✅ 支持（关键：支持 C4_Anchored 不可移动保护）

---

### 7. Journey Execution / Current Activity ✓

**模型覆盖：**
- `JourneyTwin` 投影存在
- 字段：currentActivityId, nextActivityId, nextHardCommitmentId, delayMinutes, healthStatus

**证据：**
```yaml
entities:
  JourneyTwin:
    identity: journeyTwinId
    purpose: Read-optimised projection...
    fields:
      currentActivityId: entityRef[Activity]
      nextActivityId: entityRef[Activity]
      nextHardCommitmentId: entityRef[Commitment]
      delayMinutes: integer (required)
      healthStatus: enumRef[journey_health]
```

**状态：** ✅ 支持

---

### 8. Event 机制 ✓

**模型覆盖：**
- `Event` 实体存在
- 字段：kind, occurredAt, observedAt, impactLevel, source, payload, confidence, affectedActivityIds, processingStatus, acknowledged

**证据：**
```yaml
enums:
  event_kind:
  - weather_change
  - place_closed
  - service_unavailable
  - transit_delay
  - activity_overrun
  - location_deviation
  - booking_change
  - payment_failed
  - preference_changed
  - budget_risk
  - opportunity_window_opened

entities:
  Event:
    identity: eventId
    fields:
      kind: enumRef[event_kind]
      impactLevel: enumRef[event_impact_level]
      affectedActivityIds: array[entityRef[Activity]]
```

**状态：** ✅ 支持

---

### 9. Replan Proposal ✓

**模型覆盖：**
- `ReplanProposal` 实体存在
- 字段：replanScope, triggerEventIds, basePlanVersionId, selectedCandidatePlanId, status, affectedCommitmentIds
- 生命周期：draft → awaiting_confirmation → accepted / rejected / expired / no_feasible_plan

**证据：**
```yaml
entities:
  ReplanProposal:
    identity: proposalId
    fields:
      replanScope: enumRef[replan_scope]
      triggerEventIds: array[entityRef[Event]]
      basePlanVersionId: entityRef[PlanVersion]
      selectedCandidatePlanId: entityRef[CandidatePlan]
      status: enumRef[proposal_status]
```

**状态：** ✅ 支持

---

### 10. CandidatePlan / ScoreBreakdown ✓

**模型覆盖：**
- `CandidatePlan` 实体存在
- 字段：rank, feasibility, finalScore, scoreDelta, changeCount, rationale, scoreBreakdown, preservedCommitmentCount, affectedCommitmentCount

**证据：**
```yaml
entities:
  CandidatePlan:
    identity: candidatePlanId
    fields:
      rank: integer (required)
      feasibility: boolean (required)
      finalScore: decimal (required)
      scoreBreakdown: valueObjectRef[ScoreBreakdown]
      preservedCommitmentCount: integer (required)
      affectedCommitmentCount: integer (required)
```

**状态：** ✅ 支持

---

### 11. Deterministic Feasibility ✓

**模型覆盖：**
- `Constraint` 实体存在
- 字段：kind, severity, expression, priority, source, active, relaxationPolicy, weight, violationPenalty

**证据：**
```yaml
enums:
  constraint_severity:
  - system_hard
  - commitment_hard
  - soft

  constraint_relaxation_policy:
  - never
  - exception_only
  - weighted_penalty

domain_rules:
- id: DR-001
  name: Hard constraints and Exception Mode
  rule: system_hard constraints are never relaxed...
```

**状态：** ✅ 支持

---

### 12. User Accept / New PlanVersion ✓

**模型覆盖：**
- 状态机转换支持 traveler_accepts 事件
- PlanVersion 不可变性（DR-009）："An activated PlanVersion is immutable. Accepting a replan creates and activates a new PlanVersion"

**证据：**
```yaml
state_machines:
  ReplanProposal:
    transitions:
    - from: awaiting_confirmation
      event: traveler_accepts
      to: accepted

  PlanVersion:
    invariants:
    - an activated PlanVersion is immutable
    - at most one PlanVersion is active for a Journey at a time
```

**状态：** ✅ 支持

---

### 13. JourneyTwin Refresh ✓

**模型覆盖：**
- JourneyTwin 是投影，不是独立事实源
- DR-007: "JourneyTwin projects real-time context from the newest non-expired ContextSnapshot"

**证据：**
```yaml
entities:
  JourneyTwin:
    purpose: Read-optimised projection of the journey's active plan, activities, commitments, constraints, events and latest valid context snapshot; it is not an independent source of truth.

domain_rules:
- id: DR-007
  name: Context freshness
  rule: JourneyTwin projects real-time context from the newest non-expired ContextSnapshot.
```

**状态：** ✅ 支持

---

### 14. Frontend / MCP 读取一致性

**模型覆盖：**
- 模型定义了 JourneyTwin 作为前端读取的优化投影
- 关键约束：JourneyTwin 不是独立事实源，必须与 Journey/PlanVersion 保持一致

**状态：** ⚠️ 模型层面支持，但需要实际实现验证

---

## Golden Scenario 覆盖总结

| 步骤 | 功能 | 模型支持 |
|------|------|----------|
| 1 | Journey 创建 | ✅ |
| 2 | Plan 生成 | ✅ |
| 3 | PlanVersion | ✅ |
| 4 | Booking | ✅ |
| 5 | Payment | ✅ |
| 6 | Commitment | ✅ |
| 7 | Journey Execution | ✅ |
| 8 | Event | ✅ |
| 9 | Replan | ✅ |
| 10 | CandidatePlan | ✅ |
| 11 | Feasibility | ✅ |
| 12 | User Accept | ✅ |
| 13 | JourneyTwin | ✅ |
| 14 | Frontend/MCP | ⚠️ |

## 发现的问题

### P1: JourneyTwin 一致性问题

**问题描述：**
模型明确定义 JourneyTwin 是"read-optimised projection，不是 independent source of truth"，但没有明确约束：
- JourneyTwin 的 currentActivityId/nextActivityId 如何与 PlanVersion 中的 Activity 保持同步
- 如果 Journey 状态改变，JourneyTwin 何时刷新

**建议：**
在模型中增加不变量约束，定义 JourneyTwin 刷新的触发条件和一致性规则。

### P2: 重复 Accept 防护

**问题描述：**
模型中 ReplanProposal 状态机定义了 `traveler_accepts` 从 `awaiting_confirmation` 到 `accepted` 的转换，但没有明确：
- 同一个 Proposal 能否被 Accept 两次
- Accept 后原 CandidatePlan/PlanVersion 的处理

**建议：**
增加状态机约束或业务规则，明确 Idempotency 要求。

### P3: 事件重复处理

**问题描述：**
Event 有 `processingStatus` 枚举（received, validated, processed, ignored, expired），但没有明确：
- 相同 Event 重复到达时的处理策略
- out-of-order Event 的处理

**建议：**
增加业务规则或约束定义。

---

## 结论

**Golden Scenario 状态：模型层面基本完整**

CityNexus 领域模型 v0.4.2 提供了完整的实体、关系、状态机和业务规则来支持 Golden Scenario 的核心流程。关键保护机制已就位：
- C4_Anchored 承诺不可移动
- PlanVersion 不可变性
- 确定性可行性检查
- 用户确认才能变更

**待验证：**
- 实际实现与模型的一致性
- Frontend/MCP 是否正确读取 JourneyTwin
- 事件处理的边界情况