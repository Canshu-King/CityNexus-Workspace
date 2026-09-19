# CityNexus — Design System Backlog

**生成时间**: 2026-09-12 23:58  
**范围**: 21 个核心组件 + 设计一致性审查  
**用途**: 指导 Storybook 故事补充和 UI 一致性修复

---

## 组件状态覆盖缺口

### P0 核心组件（本周完成）

#### 1. ActivityCard

**当前状态**: 仅有 default  
**缺失状态**: loading, empty, error, offline, stale, risk, protected, disabled, mobile

**故事清单**:
```tsx
// ActivityCard.stories.tsx
export const Loading: Story = {
  args: {
    activity: { id: 'A1', name: 'Loading...', status: 'loading' },
    isLoading: true,
  },
};

export const Empty: Story = {
  args: {
    activity: null,
    emptyMessage: 'No activities scheduled',
  },
};

export const Error: Story = {
  args: {
    activity: { id: 'A1', name: 'Failed Activity' },
    error: 'Failed to load details',
  },
};

export const Offline: Story = {
  args: {
    activity: { id: 'A1', name: 'Cached Activity' },
    isOffline: true,
    lastSyncedAt: new Date('2026-09-12T10:00:00Z'),
  },
};

export const Stale: Story = {
  args: {
    activity: { id: 'A1', name: 'Potentially Outdated' },
    isStale: true,
    lastVerifiedAt: new Date('2026-09-11T10:00:00Z'),
  },
};

export const Risk: Story = {
  args: {
    activity: { id: 'A1', name: 'At Risk Activity' },
    riskLevel: 'high',
    riskReason: 'Running late',
  },
};

export const Protected: Story = {
  args: {
    activity: { id: 'A1', name: 'Locked Activity' },
    isProtected: true,
    protectionReason: 'Booked and paid',
  },
};

export const Disabled: Story = {
  args: {
    activity: { id: 'A1', name: 'Unavailable' },
    isDisabled: true,
    disabledReason: 'Venue closed',
  },
};

export const Mobile: Story = {
  args: {
    activity: { id: 'A1', name: 'Mobile View' },
    viewport: 'mobile',
  },
  parameters: {
    viewport: { defaultViewport: 'mobile1' },
  },
};
```

---

#### 2. JourneyLeg

**当前状态**: 仅有 default  
**缺失状态**: loading, empty, error, offline, stale, risk, protected, disabled, mobile

**特殊状态**:
- `stale`: 路线数据超过 2 小时未更新
- `risk`: 时间不足或交通延误
- `mixed-provenance`: 多提供者混合路线

---

#### 3. CommitmentCard

**当前状态**: 仅有 default  
**缺失状态**: loading, empty, error, offline, stale, risk, protected, disabled, mobile

**特殊状态**:
- `pending-confirmation`: 等待用户确认
- `imported`: 从外部导入的预订
- `expiring-soon`: 取消期限临近

---

### P1 重要组件（下周完成）

#### 4. RiskBanner

**当前状态**: error, risk  
**缺失状态**: default, loading, empty, offline, stale, protected, disabled, mobile

**说明**: 此组件主要用于警告，default/empty 状态可能不适用

---

#### 5. AgentAction

**当前状态**: 仅有 default  
**缺失状态**: loading, empty, error, offline, stale, risk, protected, disabled, mobile

**特殊状态**:
- `pending-user-input`: 等待用户输入
- `executing`: Agent 正在执行操作
- `completed`: 操作已完成

---

#### 6. InboxArtifact

**当前状态**: 仅有 default  
**缺失状态**: loading, empty, error, offline, stale, risk, protected, disabled, mobile

**特殊状态**:
- `unprocessed`: 新导入未处理
- `processing`: OCR/解析中
- `requires-attention`: 需要用户确认

---

#### 7. WalletTicket

**当前状态**: 仅有 default  
**缺失状态**: loading, empty, error, offline, stale, risk, protected, disabled, mobile

**特殊状态**:
- `expired`: 票券已过期
- `used`: 已使用
- `expiring-soon`: 即将过期

---

#### 8. HotelCard

**当前状态**: 仅有 default  
**缺失状态**: loading, empty, error, offline, stale, risk, protected, disabled, mobile

**特殊状态**:
- `quote-expired`: 报价已过期
- `sold-out`: 房型售罄
- `price-changed`: 价格变化

---

#### 9. ModeComparison

**当前状态**: 仅有 default  
**缺失状态**: loading, empty, error, offline, stale, risk, protected, disabled, mobile

**特殊状态**:
- `calculating`: 正在计算各模式
- `incomplete`: 部分模式数据缺失

---

#### 10. ApprovalSheet

**当前状态**: 仅有 default  
**缺失状态**: loading, empty, error, offline, stale, risk, protected, disabled, mobile

**特殊状态**:
- `pending-approval`: 等待批准
- `approved`: 已批准
- `rejected`: 已拒绝
- `expired`: 批准已过期

---

### P2 辅助组件（下下周完成）

#### 11. OfflineBanner

**当前状态**: offline  
**缺失状态**: default, loading, error, stale, risk, protected, disabled, mobile

**说明**: 此组件专用于离线状态，其他状态可能不适用

---

#### 12. ProviderFreshness

**当前状态**: stale  
**缺失状态**: default, loading, error, offline, risk, protected, disabled, mobile

**特殊状态**:
- `fresh`: 数据新鲜（<30 分钟）
- `aging`: 数据开始变旧（30-60 分钟）
- `stale`: 数据过时（>60 分钟）
- `expired`: 数据已失效（>24 小时）

---

#### 13. EdgeStatus

**当前状态**: 全新组件，需实现所有状态  
**必需状态**: default, loading, error, offline, stale, risk, protected, disabled, mobile

**说明**: Edge 设备连接状态指示器

---

#### 14. TravelerTwinPreference

**当前状态**: 仅有 default  
**缺失状态**: loading, empty, error, offline, stale, risk, protected, disabled, mobile

---

## UI 一致性审查

### 间距不一致

**问题**:
- 组件内边距使用混用：`p-4`, `p-[16px]`, `padding: 16px`
- 组件外边距不统一：`m-4`, `my-4`, `gap-4`

**修复方案**:
```ts
// frontend/src/styles/spacing.ts
export const spacing = {
  xs: '4px',
  sm: '8px',
  md: '16px',
  lg: '24px',
  xl: '32px',
  '2xl': '48px',
} as const;
```

**行动**:
- [ ] 创建间距设计令牌
- [ ] 编写 ESLint 规则禁止硬编码间距值
- [ ] 逐步迁移现有组件

---

### 排版不一致

**问题**:
- 字体大小混用：`text-sm`, `text-[14px]`, `font-size: 14px`
- 字重不统一：`font-medium`, `font-semibold`, `font-weight: 500`
- 行高不一致：`leading-tight`, `leading-normal`, `line-height: 1.5`

**修复方案**:
```ts
// frontend/src/styles/typography.ts
export const typography = {
  xs: { fontSize: '12px', lineHeight: '16px', fontWeight: 400 },
  sm: { fontSize: '14px', lineHeight: '20px', fontWeight: 400 },
  base: { fontSize: '16px', lineHeight: '24px', fontWeight: 400 },
  md: { fontSize: '18px', lineHeight: '28px', fontWeight: 500 },
  lg: { fontSize: '20px', lineHeight: '28px', fontWeight: 500 },
  xl: { fontSize: '24px', lineHeight: '32px', fontWeight: 600 },
  '2xl': { fontSize: '30px', lineHeight: '36px', fontWeight: 600 },
} as const;
```

**行动**:
- [ ] 创建排版设计令牌
- [ ] 更新所有标题组件
- [ ] 添加排版预览故事

---

### 颜色语义不一致

**问题**:
- 同一种颜色多种写法：`text-red-500`, `text-[#ef4444]`, `color: red`
- 状态颜色不统一：错误有时用红色，有时用橙色
- 主题色不一致：主色调在不同组件中略有差异

**修复方案**:
```ts
// frontend/src/styles/colors.ts
export const colors = {
  // 功能色
  primary: 'var(--color-primary)',
  secondary: 'var(--color-secondary)',
  success: 'var(--color-success)',
  warning: 'var(--color-warning)',
  error: 'var(--color-error)',
  info: 'var(--color-info)',
  
  // 文本色
  textPrimary: 'var(--color-text-primary)',
  textSecondary: 'var(--color-text-secondary)',
  textDisabled: 'var(--color-text-disabled)',
  
  // 背景色
  bgPrimary: 'var(--color-bg-primary)',
  bgSecondary: 'var(--color-bg-secondary)',
  bgMuted: 'var(--color-bg-muted)',
} as const;
```

**行动**:
- [ ] 创建颜色设计令牌（CSS 变量）
- [ ] 定义语义映射
- [ ] 迁移所有硬编码颜色

---

### 按钮层级不一致

**问题**:
- 主要操作有时用实心按钮，有时用轮廓按钮
- 危险操作没有统一的红色标识
- 按钮尺寸不统一：`btn-sm`, `h-8`, `padding: 8px 16px`

**修复方案**:
```tsx
// frontend/src/components/Button/Button.tsx
type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps {
  variant?: ButtonVariant;
  size?: ButtonSize;
  // ...
}
```

**行动**:
- [ ] 统一按钮变体定义
- [ ] 制定按钮使用指南（何时用 primary/secondary/danger）
- [ ] 添加所有变体故事

---

### 图标使用不一致

**问题**:
- 同一功能不同图标：关闭用 × 或 close 图标
- 图标尺寸不统一：`w-4`, `w-[16px]`, `width: 16px`
- 图标与文本对齐不一致

**修复方案**:
```tsx
// frontend/src/components/Icon/Icon.tsx
interface IconProps {
  name: keyof typeof icons;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

// 统一图标尺寸
const iconSizes = {
  sm: '16px',
  md: '20px',
  lg: '24px',
} as const;
```

**行动**:
- [ ] 创建图标映射表
- [ ] 统一图标尺寸
- [ ] 添加图标库故事

---

### 文案风格不一致

**问题**:
- 语气不统一：有时正式，有时随意
- 错误信息格式不一致
- 中英文混排格式不统一

**修复方案**:
```md
# CityNexus 文案指南

## 语气
- 友好但专业
- 使用"您"而非"你"
- 避免技术术语（用户可见文案）

## 错误信息格式
- 标题：简短描述问题
- 正文：解释原因 + 建议操作
- 示例："无法加载行程\n网络超时，请检查连接后重试"

## 中英文混排
- 中文前后加空格：`使用 Google Maps 导航`
- 专有名词保持英文：`Check-in`, `PlanVersion`
```

**行动**:
- [ ] 编写文案指南
- [ ] 创建文案审查清单
- [ ] 逐步更新现有文案

---

### 移动端触摸目标不一致

**问题**:
- 按钮高度不统一：有些<44px（WCAG 标准）
- 链接间距过小，容易误触
- 移动端未优化触摸反馈

**修复方案**:
```ts
// frontend/src/styles/touch.ts
export const touchTargets = {
  sm: '44px',  // 最小可接受尺寸
  md: '48px',  // 推荐尺寸
  lg: '56px',  // 主要操作
} as const;
```

**行动**:
- [ ] 审查所有交互元素触摸目标
- [ ] 添加移动端故事（使用 viewport 参数）
- [ ] 添加触摸反馈动画

---

## 优先级矩阵

| 任务 | 优先级 | 预计工时 | 依赖 |
|------|--------|----------|------|
| ActivityCard 状态故事 | P0 | 4h | 无 |
| JourneyLeg 状态故事 | P0 | 4h | 无 |
| CommitmentCard 状态故事 | P0 | 4h | 无 |
| 间距设计令牌 | P1 | 2h | 无 |
| 排版设计令牌 | P1 | 2h | 无 |
| 颜色设计令牌 | P1 | 4h | 无 |
| 按钮层级统一 | P1 | 3h | 颜色令牌 |
| 文案指南 | P2 | 2h | 无 |
| 移动端触摸目标审查 | P2 | 4h | 无 |

**总预计工时**: 29 小时

---

## 下一步行动

1. **今天**: 完成 ActivityCard 的 9 种状态故事
2. **明天**: 完成 JourneyLeg 和 CommitmentCard
3. **本周**: 完成所有 P0 组件
4. **下周**: 创建设计令牌并逐步迁移

---

**备注**: 所有新故事需通过视觉回归测试。
