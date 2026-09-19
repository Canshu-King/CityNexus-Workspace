# CityNexus 红队发现报告

## 概述

本文档记录在 CityNexus 领域模型、需求和用例规范中发现的问题和潜在缺陷。

---

## 发现的问题

### P1: JourneyTwin 一致性约束缺失

**严重程度:** P1

**位置:** `domain-model/citynexus-core-domain-model-v0.4.2.yaml` - JourneyTwin 实体

**问题描述:**
模型定义 JourneyTwin 为"read-optimised projection，不是 independent source of truth"，但缺少明确的不变量约束来定义：
1. JourneyTwin 的 currentActivityId/nextActivityId 如何与 PlanVersion 中的 Activity 保持同步
2. Journey 状态改变时，JourneyTwin 刷新的触发条件
3. 如果 JourneyTwin 和 Journey 数据不一致，哪个是权威

**影响:**
- 实现时可能出现 JourneyTwin 和 Journey 数据不一致
- 前端可能显示过期的 current/next activity

**建议修复:**
在 JourneyTwin 实体中增加不变量约束：
```yaml
invariants:
- currentActivityId references an Activity in the active PlanVersion
- nextActivityId references the Activity that follows currentActivityId in the active PlanVersion
- generatedAt is updated when Journey status changes or activePlanVersionId changes
```

---

### P2: ReplanProposal 重复 Accept 防护缺失

**严重程度:** P1

**位置:** `domain-model/citynexus-core-domain-model-v0.4.2.yaml` - ReplanProposal 状态机

**问题描述:**
ReplanProposal 状态机定义了 `traveler_accepts` 从 `awaiting_confirmation` 到 `accepted` 的转换，但缺少：
1. 同一个 Proposal 能否被 Accept 两次的约束
2. Accept 后原 CandidatePlan/PlanVersion 的处理规则
3. Idempotency 保证

**影响:**
- Agent 或自动化流程可能重复 Accept 同一个 Proposal
- 可能导致意外的状态变更

**建议修复:**
在 ReplanProposal 状态机或 invariant 中增加：
```yaml
invariants:
- once status=accepted, traveler_accepts transition is no longer valid
- accepted proposals must not be mutated
```

---

### P3: Event 重复处理和 Out-of-Order 处理

**严重程度:** P2

**位置:** `domain-model/citynexus-core-domain-model-v0.4.2.yaml` - Event 实体

**问题描述:**
Event 有 `processingStatus` 枚举（received, validated, processed, ignored, expired），但没有明确：
1. 相同 Event 重复到达时的处理策略
2. out-of-order Event 的处理（例如，旧的 delay event 在新的之后到达）
3. Event 去重的机制

**影响:**
- 重复事件可能导致重复的 ReplanProposal
- 过时的事件可能覆盖新的状态

**建议修复:**
增加业务规则或约束：
```yaml
domain_rules:
- id: DR-011
  name: Event idempotency
  rule: Duplicate events with the same eventId are ignored. Events are processed in occurredAt order.
```

---

### P4: TimeWindow datetime 时区默认行为

**严重程度:** P2

**位置:** `domain-model/citynexus-core-domain-model-v0.4.2.yaml` - TimeWindow value object

**问题描述:**
TimeWindow 定义了 `timezone: IANA timezone` 字段，但：
1. datetime 字段本身没有明确是 UTC 还是本地时间
2. 如果 timezone 字段为 null 时的默认行为未定义

**影响:**
- 实现时可能出现时区混淆
- 跨时区 Journey 可能出现时间计算错误

**建议修复:**
在模型中增加说明或约束：
```yaml
value_objects:
  TimeWindow:
    fields:
      start:
        type: datetime
        description: ISO 8601 datetime, recommended to include timezone offset
      timezone:
        type: IANA timezone
        description: Required if start/end do not include timezone offset
```

---

### P5: ContextSnapshot 数据新鲜度阈值

**严重程度:** P2

**位置:** `domain-model/citynexus-core-domain-model-v0.4.2.yaml` - ContextSnapshot 实体

**问题描述:**
ContextSnapshot 有 `dataFreshness` 字段（duration 类型），但没有定义：
1. 什么是"可接受"的数据新鲜度
2. JourneyTwin 应该使用哪个 ContextSnapshot 的规则
3. 数据过期时的 fallback 行为

**影响:**
- JourneyTwin 可能使用过期的 ContextSnapshot
- 决策基于过时数据可能导致错误

**建议修复:**
增加业务规则：
```yaml
domain_rules:
- id: DR-012
  name: ContextSnapshot freshness threshold
  rule: JourneyTwin uses the newest ContextSnapshot with dataFreshness <= 15 minutes. Older snapshots are marked as stale.
```

---

### P6: Commitment 和 Activity 绑定不完整

**严重程度:** P2

**位置:** `domain-model/citynexus-core-domain-model-v0.4.2.yaml` - Commitment 实体

**问题描述:**
Commitment 有 `binds_to_activity` 关系（0..1），但：
1. 没有明确一个 Activity 最多绑定多少个 Commitment
2. 没有明确 Commitment 移动时，绑定关系如何处理

**影响:**
- 可能出现多个 C4_Anchored 绑定到同一个 Activity，阻止该 Activity 调整
- Activity 重新调度时，Commitment 绑定关系可能失效

**建议修复:**
增加约束：
```yaml
entities:
  Commitment:
    invariants:
    - An Activity may have at most one C4_Anchored commitment bound to it
    - When an Activity is rescheduled, bound C3+ commitments must be explicitly confirmed
```

---

### P7: PlanVersion 替换时 Activity ID 处理

**严重程度:** P1

**位置:** `domain-model/citynexus-core-domain-model-v0.4.2.yaml` - PlanVersion 实体

**问题描述:**
模型定义了 PlanVersion 不可变性（DR-009），但没有明确：
1. 新 PlanVersion 中的 Activity 是否可以使用新的 activityId
2. JourneyTwin 中的 currentActivityId/nextActivityId 在 PlanVersion 替换时如何更新

**影响:**
- 接受 Replan 后，前端可能仍然显示旧的 activityId
- JourneyTwin 可能引用已 superseded 的 PlanVersion 中的 Activity

**建议修复:**
增加业务规则：
```yaml
domain_rules:
- id: DR-013
  name: PlanVersion replacement activity mapping
  rule: When a new PlanVersion is activated, JourneyTwin.currentActivityId and nextActivityId must be updated to reference Activities in the new PlanVersion. The new PlanVersion should preserve Activity IDs where possible for audit continuity.
```

---

### P8: Preference 权重验证缺失

**严重程度:** P3

**位置:** `domain-model/citynexus-core-domain-model-v0.4.2.yaml` - Preference 实体

**问题描述:**
Preference 有 `weight` 字段（decimal），但没有：
1. 权重范围约束（例如 0-1 或 0-100）
2. 同一 dimension 多个 Preference 时的处理规则

**影响:**
- 权重可能超出合理范围
- 评分计算可能出现异常

**建议修复:**
增加约束：
```yaml
entities:
  Preference:
    invariants:
    - weight is in range [0.0, 1.0]
    - For a given journey and dimension, at most one non-temporary Preference applies
```

---

## 问题汇总

| ID | 问题 | 严重程度 | 状态 |
|----|------|----------|------|
| P1 | JourneyTwin 一致性约束缺失 | P1 | 待修复 |
| P2 | ReplanProposal 重复 Accept 防护缺失 | P1 | 待修复 |
| P3 | Event 重复处理和 Out-of-Order 处理 | P2 | 待修复 |
| P4 | TimeWindow datetime 时区默认行为 | P2 | 待修复 |
| P5 | ContextSnapshot 数据新鲜度阈值 | P2 | 待修复 |
| P6 | Commitment 和 Activity 绑定不完整 | P2 | 待修复 |
| P7 | PlanVersion 替换时 Activity ID 处理 | P1 | 待修复 |
| P8 | Preference 权重验证缺失 | P3 | 待修复 |

---

## 验证状态

所有发现的问题均为**模型层面**的潜在问题，不影响当前验证脚本的通过。这些问题需要在实现阶段特别注意。

**测试验证状态:**
- ✅ Domain Model 验证: 34/34 PASS
- ✅ Requirements 验证: 28/28 PASS
- ✅ Use Cases 验证: 16/16 PASS
- ✅ Visio Spec 验证: 10/10 PASS