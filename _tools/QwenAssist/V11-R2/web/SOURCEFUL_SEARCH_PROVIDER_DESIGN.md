# CityNexus — Sourceful Search Provider Design

**生成时间**: 2026-09-13  
**范围**: 有来源的网络搜索提供者设计  
**用途**: 实现可信的网络信息获取

---

## 1. 搜索提供者架构

### 1.1 提供者选项

| 提供者 | 类型 | 许可证 | 适用场景 |
|--------|------|--------|----------|
| DeepSeek 内置 | LLM 原生 | 商业 | 快速语义搜索 |
| SearXNG | 自托管元搜索 | AGPL-3.0 | 多源聚合 |
| Tavily | 专用搜索 API | 商业 | 结构化结果 |
| SerpAPI | 搜索引擎 API | 商业 | Google 结果 |

### 1.2 推荐方案

**短期**: DeepSeek 内置搜索（已集成）  
**中期**: SearXNG 自托管（开源、可控）  
**长期**: 多提供者冗余

---

## 2. WebObservation 数据结构

```python
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

class SourceCredibility(Enum):
    """来源可信度"""
    OFFICIAL = "official"           # 官方网站
    AUTHORITY = "authority"         # 权威媒体/机构
    COMMUNITY = "community"         # 社区验证
    SEO_SPAM = "seo_spam"           # SEO 垃圾内容
    UNVERIFIED = "unverified"       # 未验证

@dataclass
class WebObservation:
    """网络观察结果"""
    # 基础信息
    url: str
    title: str
    domain: str
    snippet: str
    
    # 来源分类
    source_credibility: SourceCredibility
    is_official: bool
    is_social: bool
    is_cached: bool
    
    # 时间信息
    published_at: Optional[datetime]
    fetched_at: datetime
    cache_age_hours: Optional[int]
    
    # 内容分析
    language: str
    content_type: str  # article, blog, forum, etc.
    has_prompt_injection: bool
    
    # 语义信息（DeepSeek 填充）
    semantic_summary: Optional[str]
    entities: list[dict]
    claims: list[dict]
    
    # 溯源
    provider_key: str
    query_id: str
    confidence: float  # 0-1
```

---

## 3. 查询流程

```
用户查询
    │
    ▼
┌─────────────────┐
│  查询预处理     │──▶ 关键词提取
│  (Preprocess)  │──▶ 语言检测
└─────────────────┘    │意图分类
    │                 
    ▼                 
┌─────────────────┐
│  多源搜索       │
│  (Multi-Source) │
└─────────────────┘
    │
    ├─▶ DeepSeek 内置搜索
    ├─▶ SearXNG API
    └─▶ 备用源
    │
    ▼
┌─────────────────┐
│  来源分类       │
│  (Classify)     │
└─────────────────┘
    │
    ├─▶ 官方域名匹配
    ├─▶ WHOIS 分析
    └─▶ 内容质量评估
    │
    ▼
┌─────────────────┐
│  语义理解       │
│  (Semantic)     │
└─────────────────┘
    │
    ├─▶ DeepSeek 摘要
    ├─▶ 实体提取
    └─▶ claim 验证
    │
    ▼
┌─────────────────┐
│  结果聚合       │
│  (Aggregate)    │
└─────────────────┘
    │
    ▼
WebObservation[]
```

---

## 4. 来源分类器

### 4.1 官方域名识别

```python
OFFICIAL_DOMAINS = {
    "gov.cn": ["gov.cn", "gov.*.cn"],
    "airline": ["airchina.com", "china-eastern.com", "csair.com"],
    "hotel": ["booking.com", "hotels.com", "ctrip.com", "dianping.com"],
    "attraction": ["*museum*.cn", "*park*.cn"],
}

def classify_domain(domain: str) -> SourceCredibility:
    for category, patterns in OFFICIAL_DOMAINS.items():
        for pattern in patterns:
            if "*" in pattern:
                # 通配符匹配
                if re.match(pattern.replace("*", ".*"), domain):
                    return SourceCredibility.OFFICIAL
            elif pattern == domain:
                return SourceCredibility.OFFICIAL
    
    return SourceCredibility.UNVERIFIED
```

### 4.2 SEO 垃圾检测

```python
SEO_SPAM_INDICATORS = [
    "keyword stuffing",
    "hidden text",
    "doorway pages",
    "link farm",
    "ai-generated content",
]

def detect_seo_spam(content: str, density: float) -> bool:
    if density > 0.05:  # 关键词密度过高
        return True
    
    for indicator in SEO_SPAM_INDICATORS:
        if indicator in content.lower():
            return True
    
    return False
```

---

## 5. 提示注入检测

```python
PROMPT_INJECTION_PATTERNS = [
    r"ignore (previous|above|all) (instructions?|rules?|commands?)",
    r"(forget|disregard) (everything|all) (you|the) (know|learned)",
    r"you are now (a different|a new|自由)",
    r"system prompt:",
    r"assistant role:",
    r"act as if",
]

def detect_prompt_injection(text: str) -> bool:
    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False
```

---

## 6. 缓存策略

```python
CACHE_TTL = {
    "official": 24 * 3600,      # 官方 24 小时
    "authority": 12 * 3600,     # 权威 12 小时
    "community": 6 * 3600,      # 社区 6 小时
    "unverified": 1 * 3600,     # 未验证 1 小时
    "seo_spam": 0,              # 不缓存
}
```

---

## 7. 下一步行动

1. **集成 SearXNG**: 部署自托管实例
2. **实现来源分类器**: 基于域名和内容
3. **添加提示注入检测**: 安全过滤
4. **建立缓存层**: Redis 缓存结果

---

**备注**: 网络搜索是 AI 幻觉的主要来源，必须有严格的来源追溯机制。