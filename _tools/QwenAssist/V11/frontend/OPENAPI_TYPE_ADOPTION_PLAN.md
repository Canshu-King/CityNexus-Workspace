# CityNexus — OpenAPI 类型采用计划

**生成时间**: 2026-09-13 00:05  
**范围**: 前端 TypeScript 类型与后端 OpenAPI Schema 同步  
**用途**: 指导类型迁移，避免类型漂移

---

## 现状分析

### 后端 OpenAPI Schema 位置

- **自动生成**: `backend/app/main.py` FastAPI 应用自动生成 `/openapi.json`
- **手动审查**: `contracts/` 目录（如有手动 schema 定义）
- **访问方式**: `GET http://localhost:8000/openapi.json`

### 前端手动类型位置

需扫描以下目录确认手动类型定义：

```bash
# 待扫描路径
frontend/src/types/
frontend/src/lib/types.ts
frontend/src/components/**/*.tsx (内联类型)
frontend/src/hooks/**/*.ts (内联类型)
```

### 已识别的类型重复（示例）

| 后端 Schema | 前端手动类型 | 文件位置 | 重复度 |
|-------------|--------------|----------|--------|
| `Journey` | `JourneyType` | `src/types/journey.ts` | 高 |
| `Activity` | `Activity` | `src/types/activity.ts` | 高 |
| `Commitment` | `CommitmentType` | `src/types/commitment.ts` | 高 |
| `PlanVersion` | `PlanVersion` | `src/types/plan.ts` | 中 |
| `Money` | `Money` | `src/types/money.ts` | 高 |

---

## 迁移策略

### 阶段 1: V11 新表面仅使用生成类型（立即生效）

**规则**:
- 所有新 API 端点必须使用 OpenAPI 生成类型
- 禁止为新表面手动声明类型
- 使用 `openapi-typescript` 或 `oazapfts` 生成

**实施步骤**:

1. **安装生成工具**:
```bash
cd frontend
npm install -D openapi-typescript
```

2. **添加生成脚本** (`package.json`):
```json
{
  "scripts": {
    "generate:types": "openapi-typescript http://localhost:8000/openapi.json -o src/generated/types.ts"
  }
}
```

3. **CI 集成**:
```yaml
# .github/workflows/type-check.yml
- name: Generate types from OpenAPI
  run: npm run generate:types
- name: Type check
  run: npm run typecheck
```

4. **新组件使用示例**:
```tsx
// 错误 ❌
interface NewJourney {
  id: string;
  name: string;
  // ...
}

// 正确 ✅
import { components } from '@/generated/types';
type NewJourney = components['schemas']['Journey'];
```

---

### 阶段 2: 高 churn 现有表面（第 2 周）

**目标**: 频繁变更的组件优先迁移

**识别标准**:
- 过去 30 天修改 >5 次的文件
- 与后端 API 紧密耦合的组件

**迁移清单**:
1. `JourneyCard.tsx` - 行程卡片
2. `ActivityList.tsx` - 活动列表
3. `CommitmentCard.tsx` - 承诺卡片
4. `PlanEditor.tsx` - 计划编辑器
5. `BookingForm.tsx` - 预订表单

**迁移步骤** (每个组件):
1. 运行 `npm run generate:types` 获取最新类型
2. 替换手动类型为生成类型
3. 修复类型不匹配（如有）
4. 运行测试验证
5. 提交代码

**示例迁移**:
```diff
- import { Activity } from '@/types/activity';
+ import { components } from '@/generated/types';
+ type Activity = components['schemas']['Activity'];

interface ActivityCardProps {
  activity: Activity;
  // ...
}
```

---

### 阶段 3: 稳定遗留表面（第 3-4 周）

**目标**: 不常变更的组件批量迁移

**识别标准**:
- 过去 90 天修改 <3 次的文件
- 功能稳定的组件

**迁移清单**:
- 所有剩余的手动类型
- 内联类型定义

**批量迁移策略**:
1. 按功能模块分组（行程、活动、预订等）
2. 每组迁移后运行完整测试套件
3. 发现不匹配时优先修正生成脚本而非手动覆盖

---

## TanStack Query 查询键规范

### 查询键结构

```ts
// frontend/src/lib/query-keys.ts
import { QueryKey } from '@tanstack/react-query';

export const queryKeys = {
  // 行程相关
  journey: {
    all: ['journeys'] as QueryKey,
    lists: () => [...queryKeys.journey.all, 'list'] as QueryKey,
    list: (filters: { travelerId: string }) => [...queryKeys.journey.lists(), filters] as QueryKey,
    details: () => [...queryKeys.journey.all, 'detail'] as QueryKey,
    detail: (id: string) => [...queryKeys.journey.details(), id] as QueryKey,
  },
  
  // 活动相关
  activity: {
    all: ['activities'] as QueryKey,
    lists: () => [...queryKeys.activity.all, 'list'] as QueryKey,
    list: (journeyId: string) => [...queryKeys.activity.lists(), journeyId] as QueryKey,
    details: () => [...queryKeys.activity.all, 'detail'] as QueryKey,
    detail: (id: string) => [...queryKeys.activity.details(), id] as QueryKey,
  },
  
  // 承诺相关
  commitment: {
    all: ['commitments'] as QueryKey,
    lists: () => [...queryKeys.commitment.all, 'list'] as QueryKey,
    list: (journeyId: string) => [...queryKeys.commitment.lists(), journeyId] as QueryKey,
    details: () => [...queryKeys.commitment.all, 'detail'] as QueryKey,
    detail: (id: string) => [...queryKeys.commitment.details(), id] as QueryKey,
  },
  
  // 提供者相关
  provider: {
    all: ['providers'] as QueryKey,
    freshness: (providerKey: string) => [...queryKeys.provider.all, providerKey, 'freshness'] as QueryKey,
  },
} as const;
```

### 查询无效化规则

```ts
// frontend/src/lib/query-invalidation.ts
import { QueryClient } from '@tanstack/react-query';
import { queryKeys } from './query-keys';

export function createQueryInvalidators(queryClient: QueryClient) {
  return {
    // 行程变更时
    invalidateJourneys: () => {
      return queryClient.invalidateQueries({ queryKey: queryKeys.journey.all });
    },
    
    // 特定行程变更时
    invalidateJourney: (journeyId: string) => {
      return Promise.all([
        queryClient.invalidateQueries({ queryKey: queryKeys.journey.detail(journeyId) }),
        queryClient.invalidateQueries({ queryKey: queryKeys.activity.list(journeyId) }),
        queryClient.invalidateQueries({ queryKey: queryKeys.commitment.list(journeyId) }),
      ]);
    },
    
    // 活动变更时
    invalidateActivities: (journeyId?: string) => {
      const queryKey = journeyId 
        ? queryKeys.activity.list(journeyId)
        : queryKeys.activity.all;
      return queryClient.invalidateQueries({ queryKey });
    },
    
    // 承诺变更时
    invalidateCommitments: (journeyId?: string) => {
      const queryKey = journeyId
        ? queryKeys.commitment.list(journeyId)
        : queryKeys.commitment.all;
      return queryClient.invalidateQueries({ queryKey });
    },
    
    // 提供者数据更新时
    invalidateProviderFreshness: (providerKey: string) => {
      return queryClient.invalidateQueries({
        queryKey: queryKeys.provider.freshness(providerKey),
      });
    },
  };
}
```

### 使用示例

```tsx
// frontend/src/hooks/use-journey.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '@/lib/query-keys';
import { createQueryInvalidators } from '@/lib/query-invalidation';
import { components } from '@/generated/types';

type Journey = components['schemas']['Journey'];

export function useJourney(journeyId: string) {
  const queryClient = useQueryClient();
  const invalidators = createQueryInvalidators(queryClient);
  
  const { data: journey, isLoading } = useQuery<Journey>({
    queryKey: queryKeys.journey.detail(journeyId),
    queryFn: () => fetchJourney(journeyId),
  });
  
  const updateMutation = useMutation({
    mutationFn: (updates: Partial<Journey>) => updateJourney(journeyId, updates),
    onSuccess: () => {
      // 无效化相关查询
      invalidators.invalidateJourney(journeyId);
    },
  });
  
  return { journey, isLoading, updateMutation };
}
```

---

## 手动类型重复检测清单

需扫描以下文件并记录手动类型：

### 待扫描文件列表

```bash
# 类型定义文件
find frontend/src -name "*.ts" -o -name "*.tsx" | grep -E "(types|interfaces)" | sort

# 组件内联类型
grep -r "interface.*{" frontend/src/components --include="*.tsx" | head -20

# Hooks 中的类型
grep -r "type.*=" frontend/src/hooks --include="*.ts" | head -20
```

### 扫描结果（待填充）

| 文件路径 | 类型名称 | 对应后端 Schema | 行动 |
|----------|----------|-----------------|------|
| `src/types/journey.ts` | `JourneyType` | `Journey` | 迁移 |
| `src/types/activity.ts` | `Activity` | `Activity` | 迁移 |
| ... | ... | ... | ... |

---

## 迁移检查清单

### 阶段 1 检查点

- [ ] 安装 `openapi-typescript`
- [ ] 添加生成脚本到 `package.json`
- [ ] 配置 CI 自动生成类型
- [ ] 所有新组件使用生成类型
- [ ] 文档化类型使用规范

### 阶段 2 检查点

- [ ] 迁移 5 个高 churn 组件
- [ ] 所有测试通过
- [ ] 无 TypeScript 错误
- [ ] 性能无回归

### 阶段 3 检查点

- [ ] 迁移所有剩余手动类型
- [ ] 删除 `src/types/` 目录（如完全迁移）
- [ ] 更新所有导入路径
- [ ] 最终类型审查

---

## 风险缓解

### 风险 1: 后端 Schema 变更导致前端构建失败

**缓解措施**:
- CI 中先运行类型生成，失败则阻止合并
- 后端 Schema 变更需提前通知前端团队
- 使用语义化版本管理 OpenAPI Schema

### 风险 2: 生成类型与业务逻辑不匹配

**缓解措施**:
- 必要时使用类型扩展而非覆盖
- 创建适配层转换数据格式
- 记录所有手动扩展的原因

```ts
// 正确：扩展生成类型
import { components } from '@/generated/types';

type ActivityWithUI = components['schemas']['Activity'] & {
  isSelected?: boolean;  // UI 状态，非后端数据
};

// 错误 ❌：覆盖生成类型
interface Activity {  // 与生成类型冲突
  id: string;
  // ... 可能与后端不一致
}
```

### 风险 3:  bundle 大小增加

**缓解措施**:
- 使用 tree-shaking 友好的导入方式
- 按需导入类型而非全部
- 监控 bundle 大小变化

---

## 成功指标

1. **类型一致性**: 0 个手动类型与后端 Schema 冲突
2. **开发效率**: 类型变更到前端更新时间 <5 分钟
3. **类型安全**: TypeScript 错误率下降 >50%
4. **代码审查**: 类型相关评论减少 >70%

---

## 时间表

| 阶段 | 开始日期 | 结束日期 | 负责人 |
|------|----------|----------|--------|
| 阶段 1: 新表面 | 2026-09-13 | 2026-09-15 | TBD |
| 阶段 2: 高 churn | 2026-09-16 | 2026-09-22 | TBD |
| 阶段 3: 稳定表面 | 2026-09-23 | 2026-10-06 | TBD |

---

**下一步**: 运行扫描脚本识别所有手动类型，填充扫描结果表格。
