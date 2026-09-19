# CityNexus — Opening Hours Implementation Notes

**生成时间**: 2026-09-13  
**范围**: 营业时间解析、GTFS 质量验证  
**用途**: 指导营业时间数据处理和 GTFS 质量门禁实现

---

## 1. Opening Hours 解析库评估

### 1.1 KDE/kopeninghours

**仓库**: https://github.com/KDE/kopeninghours  
**许可证**: LGPL-2.1+  
**语言**: C++ / Qt（KDE 生态）

**优点**:
- 业界最完整的营业时间解析库
- 支持复杂的规则表达式（openinghours 语法）
- 支持节假日、临时变更
- 活跃维护

**缺点**:
- C++/Qt 依赖，与 Python 后端集成需要绑定
- 可能需要使用 PyQt 或 SIP 包装

**CityNexus 适用性**: ⚠️ 需要绑定层，可作为长期方案

---

### 1.2 MobilityData/gtfs-validator

**仓库**: https://github.com/MobilityData/gtfs-validator  
**许可证**: Apache-2.0  
**语言**: Java

**优点**:
- 官方 GTFS 规范验证
- 全面检查数据质量
- 支持自定义规则
- 活跃维护

**缺点**:
- Java 依赖，需要 JVM
- 侧重验证而非解析

**CityNexus 适用性**: ✅ 可集成作为质量门禁

---

### 1.3 MobilityData/gtfs-realtime-bindings

**仓库**: https://github.com/MobilityData/gtfs-realtime-bindings  
**许可证**: Apache-2.0  
**语言**: 多种（Python, Java, .NET, Go, JS）

**优点**:
- GTFS Realtime 官方绑定
- 支持 TripUpdates, VehiclePositions, ServiceAlerts
- 多语言支持

**CityNexus 适用性**: ✅ 推荐用于实时交通数据

---

### 1.4 OpenTripPlanner (OTP)

**仓库**: https://github.com/opentripplanner/OpenTripPlanner  
**许可证**: LGPL-2.1  
**语言**: Java

**优点**:
- 完整的交通规划引擎
- 内置 GTFS 支持
- 可作为独立服务

**缺点**:
- 重量级，需要独立部署
- 学习曲线陡峭

**CityNexus 适用性**: ⚠️ 评估是否需要完整 OTP 功能

---

## 2. 实现建议

### 2.1 短期方案（Python 原生）

使用 Python 原生解析器处理简单场景：

```python
from datetime import time, datetime

class OpeningHours:
    """简化的营业时间解析"""
    
    def __init__(self, hours_str: str):
        self.raw = hours_str
        self.parsed = self._parse(hours_str)
    
    def _parse(self, hours_str: str) -> dict:
        # 支持格式：
        # "09:00-18:00"
        # "09:00-21:00; We 09:00-17:00"
        # "24 hours"
        # "closed"
        # "sunset-sunrise"
        pass
    
    def is_open_at(self, dt: datetime) -> bool:
        """检查指定时间是否营业"""
        pass
    
    def next_open(self, dt: datetime) -> datetime:
        """返回下次营业时间"""
        pass
```

### 2.2 中期方案（集成 kopeninghours）

通过 PyQt 绑定集成 KDE 库：

```python
# 需要额外的绑定层
import PyQt6
from KDE.kopeninghours import OpeningHoursParser

class OpeningHoursParser:
    """kopeninghours Python 绑定"""
    
    @staticmethod
    def parse(rules: str) -> OpeningHours:
        """解析营业时间规则"""
        pass
```

### 2.3 长期方案（混合架构）

- 简单场景：Python 原生解析
- 复杂场景：调用 kopeninghours 服务
- GTFS 质量：gtfs-validator
- 实时数据：gtfs-realtime-bindings

---

## 3. 关键设计原则

### 3.1 不扁平化语义

**错误做法**:
```
"周一至周五 09:00-18:00，周六 10:00-17:00" 
→ 转换为 "09:00-18:00"（丢失日期信息）
```

**正确做法**:
```python
class OpeningHoursRule:
    days: set[int]  # 0=周一, 6=周日
    start_time: time
    end_time: time
    is_exceptional: bool  # 临时变更
    holiday_name: str | None
    
# 保留完整语义
rules = [
    OpeningHoursRule(days={0,1,2,3,4}, start=time(9,0), end=time(18,0)),
    OpeningHoursRule(days={5}, start=time(10,0), end=time(17,0)),
]
```

### 3.2 未知/复杂时间保持不确定

**处理逻辑**:
- "日落时关闭" → 标记为 `DYNAMIC`，每次检查时计算
- "营业至最后一位顾客离开" → 标记为 `VARIABLE`
- "周一至周五" + "节假日" → 优先使用节假日规则

### 3.3 实时性要求

- 静态 GTFS：每日更新
- 实时 GTFS-Realtime：每 30 秒
- 临时变更：即时生效

---

## 4. 依赖关系图

```
┌─────────────────┐     ┌──────────────────┐
│  Place/Service  │────▶│  OpeningHours    │
└─────────────────┘     └──────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐     ┌──────────────────┐
│  GTFS Static    │     │  kopeninghours   │
│  (daily)        │     │  (complex rules) │
└─────────────────┘     └──────────────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────────┐
│  GTFS Realtime  │────▶│  gtfs-realtime   │
│  (30s)          │     │  bindings        │
└─────────────────┘     └──────────────────┘
         │
         ▼
┌─────────────────┐
│  gtfs-validator│
│  (quality gate)│
└─────────────────┘
```

---

## 5. 测试用例

### 5.1 简单营业时间

```python
def test_simple_hours():
    hours = OpeningHours("09:00-18:00")
    
    # 营业时间内
    assert hours.is_open_at(datetime(2026, 9, 12, 12, 0)) is True
    
    # 营业时间外
    assert hours.is_open_at(datetime(2026, 9, 12, 20, 0)) is False
```

### 5.2 复杂规则

```python
def test_complex_hours():
    hours = OpeningHours("09:00-21:00; We 09:00-17:00")
    
    # 周三使用特殊时间
    wednesday = datetime(2026, 9, 16, 12, 0)  # 周三
    assert hours.is_open_at(wednesday) is True
    
    # 周三 18:00 后关闭
    wednesday_evening = datetime(2026, 9, 16, 19, 0)
    assert hours.is_open_at(wednesday_evening) is False
```

### 5.3 节假日覆盖

```python
def test_holiday_override():
    hours = OpeningHours("09:00-18:00")
    
    # 假设 2026-10-01 是国庆节
    national_day = datetime(2026, 10, 1, 12, 0)
    
    # 节假日可能闭馆，需要查询节假日表
    is_holiday = check_national_holiday(national_day)
    
    if is_holiday:
        # 使用节假日特殊时间
        assert hours.is_open_at(national_day) is False
```

---

## 6. 下一步行动

1. **短期**: 实现 Python 原生 OpeningHours 类
2. **中期**: 评估 kopeninghours 绑定可行性
3. **长期**: 集成 gtfs-validator 作为 CI 质量门禁

---

**备注**: 营业时间处理是复杂问题，应优先保证正确性而非功能丰富度。