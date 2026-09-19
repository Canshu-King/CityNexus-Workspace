# CityNexus 代码 Bug 检查报告

**检查时间**: 2026-09-13 02:30  
**检查范围**: Backend 核心模块 + Frontend 关键组件

---

## 🚨 严重 Bug（P0 - 需立即修复）

### Bug-001: MockMobilityProvider 在生产环境被使用

**位置**: `backend/app/replanning/feasibility.py:144`

```python
mobility_provider=mobility_provider or MockMobilityProvider(),
```

**问题**:
- 当调用方未传入 `mobility_provider` 时，**默认使用 Mock 数据**
- 导致生产环境的路线计算、费用估算全部基于假数据
- 用户看到的"30 分钟路程"可能是完全错误的

**影响范围**: 所有调用 `build_context()` 和 `check_records()` 的地方

**修复建议**:
```python
# 改为抛出异常或从配置加载真实 provider
if mobility_provider is None:
    raise ValueError("mobility_provider must be provided for production use")
# 或从 settings 加载
from app.core.config import settings
mobility_provider = mobility_provider or create_provider_from_config(settings)
```

---

### Bug-002: ICS 时区解析缺少默认 UTC

**位置**: `backend/app/integrations/inbox/ics_parser.py:16-17`

```python
if decoded.tzinfo is None:
    decoded = decoded.replace(tzinfo=timezone.utc)
```

**问题**:
- 仅处理了 `datetime` 对象，**未处理 `date` 对象**
- 全天事件（`DTSTART;VALUE=DATE`）会被错误转换
- 示例：用户导入"2026-09-12 全天会议" → 被转为 `2026-09-12T00:00:00Z` → 可能偏差一天

**修复建议**:
```python
if isinstance(decoded, date) and not isinstance(decoded, datetime):
    # 全天事件应转为当天的 00:00 本地时间，而非 UTC
    decoded = datetime(decoded.year, decoded.month, decoded.day)
    # 不添加 tzinfo，由调用方根据用户时区处理
```

---

### Bug-003: Money 类型不一致

**位置**: 
- Backend: `backend/app/commerce/order_pricing.py:22` → `unit_amount_minor`
- Frontend: `frontend/src/api/citynexus.ts:4-7` → `amount_minor`

**问题**:
```python
# Backend
class PricedOrderLine:
    unit_amount_minor: int  # ✅ 正确
    line_total_minor: int   # ✅ 正确
```

```typescript
// Frontend
export interface Money {
  amount_minor: number;  // ❌ 与后端不一致
  currency: string;
}
```

**影响**: 前后端金额字段名不匹配，可能导致：
- JSON 序列化后字段丢失
- TypeScript 类型检查失效
- 金额显示为 `undefined`

**修复建议**: Frontend 改为 `unit_amount_minor` 或后端改为 `amount_minor`（推荐统一为 `amount_minor`）

---

### Bug-004: Hermes Agent 错误处理不完整

**位置**: `backend/app/agent/orchestrator.py:50-52`

```python
except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
    raise AgentRuntimeUnavailable("Hermes Agent completion failed") from exc
```

**问题**:
- 吞掉了所有异常细节，只返回通用错误
- 无法区分"网络超时"、"API Key 错误"、"响应格式错误"
- 调试时需查看源代码

**修复建议**:
```python
except httpx.HTTPStatusError as exc:
    if exc.response.status_code == 401:
        raise AgentRuntimeUnavailable("Hermes API key invalid") from exc
    elif exc.response.status_code == 429:
        raise AgentRuntimeUnavailable("Hermes API rate limited") from exc
except httpx.TimeoutException as exc:
    raise AgentRuntimeUnavailable("Hermes API timeout") from exc
except (KeyError, IndexError) as exc:
    raise AgentRuntimeUnavailable("Hermes response format invalid") from exc
```

---

## ⚠️ 中危 Bug（P1 - 需排期修复）

### Bug-005: 坐标查找可能抛出 KeyError

**位置**: `backend/app/integrations/mobility/runtime.py:26`

```python
if place is None:
    raise KeyError(f"no routable coordinates for {key}")
```

**问题**:
- 当 Place 和 CityService 都找不到时，直接抛异常
- 调用方可能未捕获 `KeyError`，导致请求失败
- 错误消息未区分"不存在"和"无坐标"

**修复建议**:
```python
if place is None:
    raise ValueError(f"Location '{key}' not found in database")
if place.latitude is None or place.longitude is None:
    raise ValueError(f"Location '{key}' has no coordinates")
```

---

### Bug-006: JourneyTwinProjection 时间戳使用 UTC

**位置**: `backend/app/execution/journey_twin.py:36`

```python
snapshot_at=datetime.now(timezone.utc).isoformat(),
```

**问题**:
- 前端显示时可能未转换到本地时区
- 用户看到"2026-09-13T02:30:00Z"而非"2026-09-13 10:30"

**修复建议**: 添加时区字段
```python
snapshot_at=datetime.now(timezone.utc).isoformat(),
snapshot_timezone="UTC",  # 新增
```

---

### Bug-007: V10LiveExecutionPanel 未处理 loading 状态

**位置**: `frontend/src/features/execution/V10LiveExecutionPanel.tsx:18`

```typescript
const now = clock.data ? new Date(clock.data.now) : null;
```

**问题**:
- `clock.isLoading` 未显示 loading 提示
- 用户看到空白或"—"可能以为功能故障

**修复建议**:
```typescript
if (clock.isLoading) {
  return <div>Loading clock...</div>;
}
```

---

## ℹ️ 低危问题（P2 - 可择机优化）

### Bug-008: 硬编码的超时时间

**位置**: `backend/app/integrations/mobility/runtime.py:56`

```python
with httpx.Client(timeout=10.0) as client:
```

**问题**:
- 10 秒可能对某些网络环境太短
- 未区分"连接超时"和"读取超时"

**建议**: 从配置读取
```python
timeout=httpx.Timeout(
    settings.mobility_provider_timeout,
    connect=settings.mobility_connect_timeout
)
```

---

### Bug-009: 缺失的 TypeScript 类型导出

**位置**: `frontend/src/api/citynexus.ts`

**问题**:
- `CityNexusApiError` 未导出给调用方
- 调用方无法精确捕获 API 错误

**建议**: 在文件末尾添加导出
```typescript
export { CityNexusApiError };
```

---

### Bug-010: 测试代码中的硬编码路径

**位置**: `backend/app/integrations/mock/providers.py:9`

```python
MOCK_ROOT = Path(__file__).resolve().parents[4] / "data" / "mock"
```

**问题**:
- 依赖固定的目录层级（4 级父目录）
- 重构或移动文件会导致路径错误

**建议**: 使用项目根目录配置
```python
from app.core.config import settings
MOCK_ROOT = settings.mock_data_root / "mock"
```

---

## 总结

| 级别 | 数量 | 主要风险 |
|------|------|----------|
| P0 | 4 | 生产环境使用假数据、时区错误、类型不匹配 |
| P1 | 3 | 异常处理不当、用户体验问题 |
| P2 | 3 | 代码质量优化 |

**最紧急修复**: Bug-001（MockMobilityProvider 默认值）
**影响最广**: Bug-002（ICS 时区解析）
**最难发现**: Bug-003（前后端类型不一致）

---

**建议行动**:
1. 立即修复 Bug-001，添加生产环境保护
2. 修复 Bug-002，避免全天事件解析错误
3. 统一 Bug-003 的字段命名
4. 为 Bug-004 添加详细错误分类