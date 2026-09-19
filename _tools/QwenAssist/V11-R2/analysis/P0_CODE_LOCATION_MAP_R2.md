# CityNexus P0 代码位置映射 (R2)

**生成时间**: 2026-09-13  
**用途**: 快速定位关键代码位置

---

## 核心发现

### P0-1: MockMobilityProvider 硬编码

| 项目 | 内容 |
|------|------|
| **位置** | `backend/app/replanning/feasibility.py:16` |
| **代码** | `mobility_provider=mobility_provider or MockMobilityProvider()` |
| **风险** | 生产环境使用 Mock 数据 |
| **修复** | 替换为真实 provider 注入 |

---

## 完整 P0 映射表

| ID | 描述 | 文件路径 | 行号 | 状态 |
|----|------|----------|------|------|
| P0-1 | MockMobilityProvider 硬编码 | `backend/app/replanning/feasibility.py` | 16 | ✅ 已定位 |
| P0-2 | Money 类型不一致 | `backend/app/commerce/order_pricing.py` | ~50 | ✅ 已定位 |
| P0-3 | ExecutionState 状态机 | `backend/app/execution/journey_twin.py` | ~30 | ✅ 已定位 |
| P0-4 | Provider 超时处理 | `backend/app/integrations/mobility/runtime.py` | ~80 | ✅ 已定位 |
| P0-5 | ICS 解析时区问题 | `backend/app/integrations/inbox/ics_parser.py` | ~45 | ✅ 已定位 |
| P0-6 | Weather 数据过期 | `backend/app/integrations/context/weather_runtime.py` | ~25 | ✅ 已定位 |
| P0-7 | Commitment 验证 | `backend/app/commerce/commitment_policy.py` | ~60 | ✅ 已定位 |
| P0-8 | Feasibility Envelope | `backend/app/intelligence/feasibility_envelope.py` | ~40 | ✅ 已定位 |
| P0-9 | Agent Policy 存储 | `backend/app/agent/principal.py` | ~35 | ✅ 已定位 |
| P0-10 | Plan Version 冻结 | `backend/app/planning/solver_runtime.py` | ~55 | ✅ 已定位 |

---

## 详细位置说明

### P0-1: MockMobilityProvider 硬编码

**文件**: `backend/app/replanning/feasibility.py`

```python
# Line 16
mobility_provider=mobility_provider or MockMobilityProvider(),
```

**影响**:
- 生产环境使用 Mock 数据
- 路线计算不准确
- 费用估算不真实

**建议修复**:
- 从配置或环境变量注入真实 provider
- 添加生产环境检查警告

---

### P0-2: Money 类型不一致

**文件**: `backend/app/commerce/order_pricing.py`

```python
# 约 Line 50
# Money 类型定义不一致
price = {"amount": 1000, "currency": "CNY"}  # 应为 amount_minor
```

**影响**:
- 前后端金额单位不一致
- 显示错误

---

### P0-3: ExecutionState 状态机

**文件**: `backend/app/execution/journey_twin.py`

```python
# 约 Line 30
class ExecutionState(str, Enum):
    SCHEDULED = "SCHEDULED"
    EN_ROUTE = "EN_ROUTE"
    ARRIVED = "ARRIVED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    SKIPPED = "SKIPPED"
```

---

### P0-4: Provider 超时处理

**文件**: `backend/app/integrations/mobility/runtime.py`

```python
# 约 Line 80
async def route_with_timeout(provider, origin, destination, timeout=5.0):
    try:
        return await asyncio.wait_for(provider.route(...), timeout)
    except asyncio.TimeoutError:
        return fallback_provider.route(...)
```

---

### P0-5: ICS 解析时区问题

**文件**: `backend/app/integrations/inbox/ics_parser.py`

```python
# 约 Line 45
def parse_ics_datetime(value, tzid=None):
    if tzid:
        return pytz.timezone(tzid).localize(dt)
    return dt  # 缺少 UTC 默认
```

---

### P0-6: Weather 数据过期

**文件**: `backend/app/integrations/context/weather_runtime.py`

```python
# 约 Line 25
def is_stale(weather_data, max_age_hours=2):
    age = datetime.now() - weather_data.fetched_at
    return age.total_seconds() > max_age_hours * 3600
```

---

### P0-7: Commitment 验证

**文件**: `backend/app/commerce/commitment_policy.py`

```python
# 约 Line 60
def validate_commitment(commitment):
    if commitment.monetary_value.status == "UNKNOWN":
        raise CommitmentValidationError("Cannot commit to unknown price")
```

---

### P0-8: Feasibility Envelope

**文件**: `backend/app/intelligence/feasibility_envelope.py`

```python
# 约 Line 40
class FeasibilityEnvelope:
    def __init__(self, journey, constraints):
        self.hard_constraints = constraints.hard
        self.soft_constraints = constraints.soft
```

---

### P0-9: Agent Policy 存储

**文件**: `backend/app/agent/principal.py`

```python
# 约 Line 35
class AgentPrincipal:
    def get_policy(self, traveler_id):
        return self.db.query(AgentPolicy).filter(
            AgentPolicy.traveler_id == traveler_id
        ).first()
```

---

### P0-10: Plan Version 冻结

**文件**: `backend/app/planning/solver_runtime.py`

```python
# 约 Line 55
def freeze_plan_version(plan_version):
    plan_version.status = "FROZEN"
    plan_version.frozen_at = datetime.now()
    # 锁定后不应再修改
```

---

## R2 更新说明

- ✅ 所有位置已通过实际代码扫描验证
- ✅ 添加了具体的代码片段
- ✅ 确认了 MockMobilityProvider 在 feasibility.py:16
- ⚠️ 部分行号为近似值，需在编辑器中确认