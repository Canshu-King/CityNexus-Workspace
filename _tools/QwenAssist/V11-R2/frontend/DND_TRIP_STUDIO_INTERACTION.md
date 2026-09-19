# CityNexus — DnD Trip Studio Interaction Specification

**生成时间**: 2026-09-13  
**范围**: 拖拽式行程编辑交互设计  
**用途**: 实现直观、安全的行程拖拽编辑体验

---

## 1. 交互流程

### 1.1 主流程

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  Drag   │───▶│ Draft   │───▶│ Preview │───▶│ Impact  │───▶│ Accept  │
│  Start  │    │ Created │    │ Request │    │ Summary │    │ or      │
└─────────┘    └─────────┘    └─────────┘    └─────────┘    │ Reject  │
                                                               └─────────┘
```

### 1.2 状态机

```python
from enum import Enum

class DragState(Enum):
    IDLE = "idle"                    # 静止状态
    DRAGGING = "dragging"            # 拖拽中
    DRAFT = "draft"                  # 草稿状态
    PREVIEWING = "previewing"        # 预览请求中
    IMPACT_SHOWN = "impact_shown"    # 影响已显示
    ACCEPTED = "accepted"            # 已接受
    REJECTED = "rejected"            # 已拒绝
    ROLLED_BACK = "rolled_back"      # 已回滚
```

---

## 2. 拖拽事件处理

### 2.1 拖拽启动

```typescript
interface DragStartEvent {
  type: "drag_start";
  activityId: string;
  position: { x: number; y: number };
  timestamp: number;
}

function handleDragStart(event: DragStartEvent): DragState {
  // 1. 记录原始位置
  originalPosition = getActivityPosition(event.activityId);
  
  // 2. 创建草稿副本（不修改 ACTIVE PlanVersion）
  draftId = createDraftPlanVersion(activePlanVersion);
  
  // 3. 设置状态
  return DragState.DRAGGING;
}
```

### 2.2 拖拽预览

```typescript
interface DragPreviewEvent {
  type: "drag_preview";
  activityId: string;
  targetPosition: { x: number; y: number };
  dropZoneId?: string;
}

function handleDragPreview(event: DragPreviewEvent): void {
  // 1. 更新草稿副本的临时位置
  updateDraftPosition(draftId, event.activityId, event.targetPosition);
  
  // 2. 显示占位符
  showPlaceholder(event.activityId, event.targetPosition);
  
  // 3. 高亮有效放置区域
  highlightValidDropZones(event.targetPosition);
}
```

### 2.3 放置事件

```typescript
interface DropEvent {
  type: "drop";
  activityId: string;
  targetPosition: { x: number; y: number };
  dropZoneId: string;
}

function handleDrop(event: DropEvent): DragState {
  // 1. 验证放置有效性
  if (!isValidDrop(event)) {
    return DragState.IDLE;
  }
  
  // 2. 创建预览请求
  previewRequest = createPreviewRequest(draftId, event);
  
  // 3. 触发影响分析
  return DragState.PREVIEWING;
}
```

---

## 3. 预览/重规划请求

### 3.1 请求结构

```typescript
interface PreviewRequest {
  draft_id: string;
  changes: PlanChange[];
  trigger: "drag_drop" | "time_change" | "remove";
  include_impact: boolean;
}

interface PlanChange {
  type: "move" | "add" | "remove" | "resize";
  activity_id: string;
  from_position?: { day: number; index: number };
  to_position?: { day: number; index: number };
}
```

### 3.2 影响摘要

```typescript
interface ImpactSummary {
  // 时间影响
  timeChanges: {
    activityId: string;
    oldTime: string;
    newTime: string;
    conflict: boolean;
  }[];
  
  // 成本影响
  costChanges: {
    oldTotal: number;
    newTotal: number;
    delta: number;
  };
  
  // 约束冲突
  constraintViolations: {
    type: "opening_hours" | "travel_time" | "protected" | "commitment";
    description: string;
    severity: "error" | "warning";
  }[];
  
  // 风险变化
  riskChanges: {
    activityId: string;
    oldRisk: number;
    newRisk: number;
  }[];
}
```

---

## 4. 冲突处理

### 4.1 冲突类型

| 冲突类型 | 检测方法 | 处理方式 |
|----------|----------|----------|
| C4 保护 | commitment.protected === true | 阻止放置，显示警告 |
| 营业时间 | checkOpeningHours() | 显示警告，允许覆盖 |
| 行程时间 | travelTime > available | 阻止放置 |
| 酒店冲突 | checkIn/CheckOut 冲突 | 显示警告 |
| 过时路线 | route.cached_at > 2h | 提示刷新 |

### 4.2 冲突解决

```typescript
function resolveConflict(conflict: Conflict): Resolution {
  switch (conflict.type) {
    case "protected":
      return {
        action: "block",
        message: "无法移动受保护的承诺",
        suggestion: "先解除保护"
      };
      
    case "opening_hours":
      return {
        action: "warn",
        message: "活动在营业时间外",
        suggestion: "调整时间或确认"
      };
      
    case "travel_time":
      return {
        action: "block",
        message: "行程时间不足",
        suggestion: "调整顺序或移除活动"
      };
      
    default:
      return {
        action: "warn",
        message: "潜在问题",
        suggestion: "确认后继续"
      };
  }
}
```

---

## 5. 接受/拒绝流程

### 5.1 接受变更

```typescript
async function acceptChanges(draftId: string): Promise<void> {
  // 1. 验证用户权限
  if (!canUserModify(userId, journeyId)) {
    throw new PermissionError();
  }
  
  // 2. 创建新 PlanVersion
  newVersion = await createPlanVersion(draftId);
  
  // 3. 原子切换
  await atomicSwitch(activePlanVersion.id, newVersion.id);
  
  // 4. 记录审计日志
  await recordAudit({
    action: "plan_version_accepted",
    userId,
    journeyId,
    draftId,
    newVersionId: newVersion.id
  });
  
  // 5. 通知相关方
  notifySubscribers(journeyId, "plan_updated");
}
```

### 5.2 拒绝/回滚

```typescript
async function rejectChanges(draftId: string): Promise<void> {
  // 1. 丢弃草稿
  await discardDraft(draftId);
  
  // 2. 恢复 UI 状态
  restoreOriginalPositions();
  
  // 3. 记录审计
  await recordAudit({
    action: "plan_version_rejected",
    userId,
    journeyId,
    draftId
  });
}
```

---

## 6. 键盘拖拽支持

### 6.1 键盘快捷键

| 操作 | 快捷键 | 说明 |
|------|--------|------|
| 选择活动 | Tab / Arrow keys | 导航 |
| 开始拖拽 | Space / Enter | 进入拖拽模式 |
| 移动 | Arrow keys | 微调位置 |
| 放置 | Space / Enter | 确认放置 |
| 取消 | Escape | 取消拖拽 |

### 6.2 焦点管理

```typescript
function handleKeyboardDrag(event: KeyboardEvent): void {
  switch (event.key) {
    case "ArrowUp":
      moveActivity(-1); // 上移
      break;
    case "ArrowDown":
      moveActivity(1);  // 下移
      break;
    case "ArrowLeft":
      moveToPreviousDay();
      break;
    case "ArrowRight":
      moveToNextDay();
      break;
    case "Escape":
      cancelDrag();
      break;
    case "Enter":
      confirmDrop();
      break;
  }
}
```

---

## 7. 移动端适配

### 7.1 触摸手势

| 手势 | 操作 |
|------|------|
| 单指拖动 | 移动活动 |
| 长按 | 进入拖拽模式 |
| 双指捏合 | 调整活动时间 |
| 边缘滑动 | 切换日期视图 |

### 7.2 触摸反馈

```typescript
function provideTouchFeedback(type: "start" | "move" | "drop"): void {
  switch (type) {
    case "start":
      // 轻微震动
      navigator.vibrate(10);
      // 放大活动卡片
      scaleActivity(1.05);
      break;
    case "move":
      // 轻微震动（穿过有效区域）
      navigator.vibrate(5);
      break;
    case "drop":
      // 成功放置震动
      navigator.vibrate([10, 50, 10]);
      break;
  }
}
```

---

## 8. 关键约束

### 8.1 绝对约束（不可违反）

- **禁止直接修改 ACTIVE PlanVersion**：所有修改通过草稿副本
- **C4 保护**：受保护的活动不可移动
- **原子切换**：PlanVersion 切换必须原子完成

### 8.2 软约束（可覆盖）

- 营业时间冲突 → 警告但可继续
- 行程时间不足 → 警告但可继续
- 价格变化 → 警告但可继续

---

## 9. 下一步行动

1. **实现拖拽状态机**: React 组件 + 状态管理
2. **集成重规划 API**: 预览请求和影响摘要
3. **添加键盘支持**: 无障碍访问
4. **移动端适配**: 触摸手势和反馈

---

**核心原则**: 拖拽操作不应直接修改 ACTIVE PlanVersion，所有变更必须经过预览 → 影响分析 → 用户确认流程。