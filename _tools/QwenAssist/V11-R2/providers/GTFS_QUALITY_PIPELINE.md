# CityNexus — GTFS Quality Pipeline

**生成时间**: 2026-09-13  
**范围**: GTFS 数据质量验证流程  
**用途**: 确保交通数据的准确性和完整性

---

## 1. GTFS 质量管道架构

### 1.1 管道阶段

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Download   │───▶│  Validate   │───▶│  Transform  │───▶│  Integrate  │
│  (Source)   │    │  (Rules)    │    │  (Normalize)│    │  (CityNexus)│
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                  │                  │                  │
       ▼                  ▼                  ▼                  ▼
   - GTFS.zip        - Schema          - CRS Transform    - Provider
   - Realtime        - Required        - ID Mapping       - JourneyLeg
                     - Consistency     - Timezone         - Activity
                     - Custom          - Currency
```

### 1.2 数据源

| 来源 | 类型 | 更新频率 | 质量等级 |
|------|------|----------|----------|
| 官方 GTFS | 静态 | 每日 | A |
| 社区 GTFS | 静态 | 不定期 | B-C |
| GTFS-Realtime | 实时 | 30s | A |
| 第三方 API | 动态 | 按需 | B |

---

## 2. Validation Rules

### 2.1 必需字段检查

```python
REQUIRED_FIELDS = {
    "routes": ["route_id", "route_short_name", "route_type"],
    "trips": ["trip_id", "route_id", "service_id"],
    "stops": ["stop_id", "stop_name", "stop_lat", "stop_lon"],
    "stop_times": ["trip_id", "stop_id", "arrival_time", "departure_time"],
    "calendar": ["service_id", "monday", "tuesday", "wednesday", 
                 "thursday", "friday", "saturday", "sunday",
                 "start_date", "end_date"],
}
```

### 2.2 数据一致性检查

```python
CONSISTENCY_CHECKS = [
    "stop_times.arrival_time >= trips.block_id.start_time",
    "stop_times.departure_time >= stop_times.arrival_time",
    "stops.stop_lat within valid range (-90, 90)",
    "stops.stop_lon within valid range (-180, 180)",
    "calendar.start_date <= calendar.end_date",
    "routes.route_type in valid_route_types",
]
```

### 2.3 自定义业务规则

```python
BUSINESS_RULES = [
    # 站点必须在中国边界内
    "stops.stop_lat between 15 and 55",
    "stops.stop_lon between 73 and 135",
    
    # 行程时间必须合理
    "stop_times.departure_time - stop_times.arrival_time >= 0",
    "stop_times.departure_time - stop_times.arrival_time <= 4 hours",
    
    # 必须有周末服务
    "calendar.saturday == 1 OR calendar.sunday == 1",
]
```

---

## 3. 质量评分

### 3.1 评分维度

| 维度 | 权重 | 指标 |
|------|------|------|
| 完整性 | 30% | 必需字段填充率 |
| 准确性 | 30% | 坐标、时间的准确性 |
| 一致性 | 20% | 内部数据一致性 |
| 时效性 | 20% | 数据更新时间 |

### 3.2 评分计算

```python
def calculate_quality_score(validation_result: dict) -> float:
    completeness = (filled_required_fields / total_required_fields) * 100
    accuracy = (valid_coordinates / total_stops) * 100
    consistency = (passed_consistency_checks / total_checks) * 100
    freshness = min(data_age_hours / 24, 1) * 100
    
    score = (
        completeness * 0.3 +
        accuracy * 0.3 +
        consistency * 0.2 +
        freshness * 0.2
    )
    
    return score
```

### 3.3 质量等级

| 等级 | 分数 | 行动 |
|------|------|------|
| A | 90-100 | 直接使用 |
| B | 70-89 | 警告后使用 |
| C | 50-69 | 需要人工审查 |
| D | <50 | 不推荐使用 |

---

## 4. 集成 gtfs-validator

### 4.1 本地验证

```bash
# 下载 validator
wget https://github.com/MobilityData/gtfs-validator/releases/latest/download/gtfs-validator.jar

# 运行验证
java -jar gtfs-validator.jar -i /path/to/gtfs.zip -o /path/to/output/
```

### 4.2 CI 集成

```yaml
# .github/workflows/gtfs-quality.yml
name: GTFS Quality Gate

on:
  schedule:
    - cron: '0 2 * * *'  # 每日凌晨
  workflow_dispatch:

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Download GTFS
        run: |
          # 下载最新 GTFS
          curl -o data/gtfs.zip $GTFS_URL
      
      - name: Run Validator
        run: |
          java -jar gtfs-validator.jar \
            -i data/gtfs.zip \
            -o data/validation_report/
      
      - name: Check Quality Score
        run: |
          python scripts/check_quality.py data/validation_report/
      
      - name: Upload Report
        uses: actions/upload-artifact@v3
        with:
          name: gtfs-validation-report
          path: data/validation_report/
```

---

## 5. 数据转换

### 5.1 坐标转换 (CRS)

```python
from pyproj import Transformer

class GTFSTransformer:
    """GTFS 坐标转换"""
    
    def __init__(self, source_crs="EPSG:4326", target_crs="EPSG:3857"):
        self.transformer = Transformer.from_crs(
            source_crs, target_crs, always_xy=True
        )
    
    def transform_stop(self, stop: dict) -> dict:
        lon, lat = stop["stop_lon"], stop["stop_lat"]
        x, y = self.transformer.transform(lon, lat)
        
        return {
            **stop,
            "stop_x": x,
            "stop_y": y,
            "stop_crs": self.target_crs
        }
```

### 5.2 时间转换

```python
from datetime import datetime, timezone

class TimezoneConverter:
    """GTFS 时间转换为 UTC"""
    
    def __init__(self, agency_timezone: str = "Asia/Shanghai"):
        self.tz = timezone(timedelta(hours=8))  # 简化
    
    def gtfs_time_to_datetime(self, date: str, gtfs_time: str) -> datetime:
        """GTFS 时间转换为 datetime
        
        GTFS 格式: HH:MM:SS (24小时制，可超过 24:00)
        """
        hours, minutes, seconds = map(int, gtfs_time.split(":"))
        
        # 处理超过 24 小时的情况（如凌晨车辆）
        days_offset = hours // 24
        hours = hours % 24
        
        dt = datetime.strptime(date, "%Y%m%d")
        dt = dt.replace(hour=hours, minute=minutes, second=seconds)
        dt = dt.replace(tzinfo=self.tz)
        
        if days_offset > 0:
            dt += timedelta(days=days_offset)
        
        return dt
```

---

## 6. 监控与告警

### 6.1 质量监控指标

```python
QUALITY_METRICS = {
    "gtfs_validation_errors": "gauge",
    "gtfs_quality_score": "gauge",
    "gtfs_data_freshness_hours": "gauge",
    "gtfs_stale_routes_count": "counter",
    "gtfs_missing_trips_count": "counter",
}
```

### 6.2 告警规则

```yaml
# Prometheus 告警规则
groups:
  - name: gtfs_quality
    rules:
      - alert: GTFSDown
        expr: gtfs_quality_score == 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "GTFS 数据源不可用"
      
      - alert: GTFSQualityDegraded
        expr: gtfs_quality_score < 70
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "GTFS 质量下降"
      
      - alert: GTFSStale
        expr: gtfs_data_freshness_hours > 24
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "GTFS 数据超过 24 小时未更新"
```

---

## 7. 下一步行动

1. **集成 gtfs-validator**: 作为每日 CI 任务运行
2. **实现转换层**: 坐标和时间转换
3. **建立监控**: 质量指标和告警
4. **文档化数据源**: 每个 GTFS 来源的质量等级

---

**备注**: GTFS 质量是交通功能的基础，应持续监控和改进。