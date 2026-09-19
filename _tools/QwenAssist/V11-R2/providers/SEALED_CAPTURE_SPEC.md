# CityNexus — Sealed Provider Capture Specification

**生成时间**: 2026-09-13  
**范围**: 提供者数据捕获、存储、回放规范  
**用途**: 实现可追溯的提供者数据管理

---

## 1. 数据类型定义

### 1.1 数据来源分类

```python
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

class DataProvenance(Enum):
    """数据来源类型"""
    LIVE_CAPTURE = "live_capture"         # 实时捕获
    CAPTURED_REPLAY = "captured_replay"   # 捕获后回放
    SYNTHETIC_FIXTURE = "synthetic_fixture"  # 合成fixture
    FALLBACK = "fallback"                 # 回退数据
    USER_IMPORTED = "user_imported"       # 用户导入
    AI_INFERRED = "ai_inferred"           # AI推断
    MIXED = "mixed"                       # 混合来源
```

### 1.2 密封捕获记录

```python
@dataclass
class SealedCapture:
    """密封的提供者捕获记录"""
    # 标识
    capture_id: str
    provider_key: str
    operation: str
    
    # 请求指纹
    request_fingerprint: str  # hash(request_params)
    request_params: dict
    
    # 原始响应
    raw_response: str
    raw_response_hash: str
    
    # 规范化数据
    normalized_facts: dict
    normalizer_version: str
    
    # 时间戳
    captured_at: datetime
    expires_at: Optional[datetime]
    
    # 地理信息
    crs: str  # 坐标参考系统
    
    # 元数据
    redaction_metadata: dict
    checksum: str
    
    # 来源追溯
    provenance: DataProvenance
    parent_capture_id: Optional[str]
```

---

## 2. Schema 定义

### 2.1 JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": [
    "capture_id",
    "provider_key",
    "operation",
    "captured_at",
    "provenance"
  ],
  "properties": {
    "capture_id": {
      "type": "string",
      "pattern": "^[a-zA-Z0-9-_]{16,64}$"
    },
    "provider_key": {
      "type": "string",
      "enum": ["valhalla", "amap", "open-meteo", "booking.com", "mock-mobility"]
    },
    "operation": {
      "type": "string",
      "enum": ["route", "estimate", "weather", "booking", "search"]
    },
    "request_fingerprint": {
      "type": "string",
      "pattern": "^[a-f0-9]{64}$"
    },
    "raw_response": {
      "type": "string"
    },
    "normalized_facts": {
      "type": "object"
    },
    "normalizer_version": {
      "type": "string",
      "pattern": "^v\\d+\\.\\d+\\.\\d+$"
    },
    "captured_at": {
      "type": "string",
      "format": "date-time"
    },
    "expires_at": {
      "type": "string",
      "format": "date-time"
    },
    "crs": {
      "type": "string",
      "default": "EPSG:4326"
    },
    "checksum": {
      "type": "string",
      "pattern": "^[a-f0-9]{64}$"
    },
    "provenance": {
      "type": "string",
      "enum": ["live_capture", "captured_replay", "synthetic_fixture", "fallback", "user_imported", "ai_inferred", "mixed"]
    }
  }
}
```

---

## 3. 验证器

### 3.1 捕获验证器

```python
import hashlib
import json
from datetime import datetime, timedelta

class CaptureValidator:
    """密封捕获验证器"""
    
    @staticmethod
    def validate(capture: SealedCapture) -> tuple[bool, list[str]]:
        """验证捕获记录完整性"""
        errors = []
        
        # 1. 校验 checksum
        expected_checksum = CaptureValidator._compute_checksum(capture)
        if capture.checksum != expected_checksum:
            errors.append(f"Checksum mismatch: expected {expected_checksum}")
        
        # 2. 校验时间有效性
        if capture.expires_at and capture.expires_at < datetime.now(timezone.utc):
            errors.append(f"Capture expired at {capture.expires_at}")
        
        # 3. 校验必填字段
        if not capture.capture_id:
            errors.append("Missing capture_id")
        if not capture.provider_key:
            errors.append("Missing provider_key")
            
        return len(errors) == 0, errors
    
    @staticmethod
    def _compute_checksum(capture: SealedCapture) -> str:
        """计算校验和"""
        content = json.dumps({
            "provider_key": capture.provider_key,
            "operation": capture.operation,
            "request_fingerprint": capture.request_fingerprint,
            "raw_response": capture.raw_response,
            "normalized_facts": capture.normalized_facts,
            "captured_at": capture.captured_at.isoformat(),
        }, sort_keys=True)
        
        return hashlib.sha256(content.encode()).hexdigest()
```

---

## 4. 混合来源处理

### 4.1 聚合来源检测

```python
def detect_mixed_provenance(legs: list[dict]) -> DataProvenance:
    """检测旅程腿的聚合来源"""
    providers = set()
    
    for leg in legs:
        if "provider_key" in leg:
            providers.add(leg["provider_key"])
    
    if len(providers) == 0:
        return DataProvenance.UNKNOWN
    elif len(providers) == 1:
        return DataProvenance.LIVE_CAPTURE
    else:
        return DataProvenance.MIXED
```

### 4.2 来源优先级

```python
PROVENANCE_PRIORITY = {
    DataProvenance.LIVE_CAPTURE: 100,
    DataProvenance.CAPTURED_REPLAY: 80,
    DataProvenance.USER_IMPORTED: 60,
    DataProvenance.AI_INFERRED: 40,
    DataProvenance.SYNTHETIC_FIXTURE: 20,
    DataProvenance.FALLBACK: 10,
    DataProvenance.MIXED: 50,  # 中等优先级
}
```

---

## 5. 存储策略

### 5.1 分层存储

| 类型 | 存储位置 | TTL | 压缩 |
|------|----------|-----|------|
| LIVE_CAPTURE | Redis | 1小时 | 无 |
| CAPTURED_REPLAY | PostgreSQL JSON | 30天 | gzip |
| SYNTHETIC_FIXTURE | 文件系统 | 永久 | 无 |
| FALLBACK | 内存缓存 | 进程生命周期 | 无 |
| USER_IMPORTED | PostgreSQL | 用户删除 | gzip |
| AI_INFERRED | PostgreSQL JSON | 7天 | gzip |

### 5.2 清理策略

```python
CLEANUP_POLICY = {
    "live_capture": "age > 1 hour",
    "captured_replay": "age > 30 days AND access_count = 0",
    "synthetic_fixture": "never (versioned)",
    "fallback": "never (in-memory)",
    "user_imported": "user_deleted OR age > 1 year",
    "ai_inferred": "age > 7 days",
}
```

---

## 6. 测试矩阵

| 测试 | 场景 | 预期结果 |
|------|------|----------|
| T1 | 有效捕获验证 | 通过 |
| T2 | Checksum 不匹配 | 失败 + 错误信息 |
| T3 | 过期捕获检测 | 警告 + 建议刷新 |
| T4 | 混合来源检测 | 返回 MIXED |
| T5 | 来源优先级排序 | 正确排序 |
| T6 | 回放一致性 | 相同输入 → 相同输出 |

---

**下一步**: 实现完整的存储后端和验证逻辑。