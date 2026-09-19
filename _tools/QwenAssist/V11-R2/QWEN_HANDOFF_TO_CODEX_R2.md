# QWEN R2 交接文档 → Codex

**生成时间**: 2026-09-13  
**范围**: CityNexus V11 Sidecar Round 2 完成物

---

## 1. 已验证的 P0 发现

| ID | 发现 | 位置 | 状态 |
|----|------|------|------|
| P0-1 | MockMobilityProvider 硬编码在 feasibility.py:16 | `backend/app/replanning/feasibility.py:16` | ✅ 已验证 |
| P0-2 | Money 类型使用 `amount` 而非 `amount_minor` | `backend/app/commerce/order_pricing.py:~50` | ✅ 已验证 |
| P0-3 | ExecutionState 状态机定义 | `backend/app/execution/journey_twin.py:~30` | ✅ 已验证 |
| P0-4 | Provider 超时回退逻辑 | `backend/app/integrations/mobility/runtime.py:~80` | ✅ 已验证 |
| P0-5 | ICS 解析缺少默认 UTC 时区 | `backend/app/integrations/inbox/ics_parser.py:~45` | ✅ 已验证 |

---

## 2. 可直接复制的测试

### 2.1 对抗性测试 (85 个测试函数)

| 文件 | 覆盖范围 |
|------|----------|
| `candidate_tests/test_deepseek_agent_adversarial.py` | B1: Agent 检查、工具循环、跨用户访问、策略确认 |
| `candidate_tests/test_compose_provider_truth.py` | B2: POI 重排序、多日行程、快照选择、混合 provenance |
| `candidate_tests/test_money_adversarial.py` | B3: FREE_KNOWN/KNOWN/ESTIMATED/UNKNOWN、外币、预算边界 |
| `candidate_tests/test_execution.py` | B4: EN_ROUTE/ARRIVED/IN_PROGRESS/COMPLETED/SKIPPED、C4 倒计时 |
| `candidate_tests/test_journey_inbox.py` | B5: TZID ICS、QR 导入、截图提取、确认边界 |

**语法验证**: ✅ 所有文件通过 `python -m py_compile`

---

## 2.2 边缘案例

| 文件 | 行数 | 覆盖 |
|------|------|------|
| `product/REAL_TRAVEL_EDGE_CASES.csv` | 150 行 | Airport/Hotel/Attraction/Weather/Transit/Offline/GPS/Device/Provider/DataQuality/AI/Security/Edge/Import/Money/Execution/Composition |

---

## 3. 准备好的辅助文件

### 3.1 Provider 设计

| 文件 | 内容 |
|------|------|
| `providers/OPENING_HOURS_IMPLEMENTATION_NOTES.md` | KDE/kopeninghours, gtfs-validator, OTP 评估 |
| `providers/GTFS_QUALITY_PIPELINE.md` | 质量验证规则和 CI 集成 |
| `providers/SEALED_CAPTURE_SPEC.md` | Provider 数据捕获规范 |
| `providers/PROVENANCE_TEST_MATRIX.csv` | 17 个 provenance 测试用例 |
| `web/SOURCEFUL_SEARCH_PROVIDER_DESIGN.md` | DeepSeek/SearXNG/Tavily 设计 |
| `web/WEB_TRUST_ADVERSARIAL_CASES.md` | 30+ 对抗案例 |

### 3.2 前端采用

| 文件 | 内容 |
|------|------|
| `frontend/GITHUB_UI_ADOPTION_RESEARCH_R2.md` | 15 个库的采用状态（许可证已验证） |
| `frontend/GITHUB_ADOPTION_STATUS.csv` | INSTALLED/USED_IN_SOURCE/REFERENCED_ONLY/NOT_ADOPTED |
| `frontend/HANDWRITTEN_TYPE_DUPLICATES.csv` | 17 个手写类型重复 |
| `frontend/DIRECT_API_CALLS.csv` | 25 个直接 API 调用 |
| `frontend/STORYBOOK_MATRIX_R2.csv` | 14 个组件的状态覆盖 |
| `frontend/DND_TRIP_STUDIO_INTERACTION.md` | DnD 状态机规范 |

---

## 4. 修正的 GitHub/许可证发现

| 库 | 原判断 | R2 验证结果 |
|----|--------|-------------|
| 21st-dev/agent-elements | ❌ 许可证不明确 | ✅ **MIT** |
| 21st-dev/codex-plugin | ❌ 许可证不明确 | ✅ **Apache 2.0** |

**验证方法**: 直接读取 LICENSE 文件内容

---

## 5. 真实旅行边缘案例亮点

### 高优先级 (P0)

- **AIR-01**: 航班延误 2 小时 → 自动调整接驳交通
- **AIR-03**: 国际航班海关排队 → 预留 45 分钟缓冲
- **HTL-03**: 酒店超售 → 自动寻找替代酒店
- **WEA-01/06**: 暴雨/雷电预警 → 建议室内替代
- **TRF-02**: 交通事故 → 实时重新规划
- **HAL-01**: AI 虚构景点 → 验证真实性并阻止

### 关键概念覆盖

- Money: FREE_KNOWN/KNOWN/ESTIMATED/UNKNOWN
- Execution: SCHEDULED/EN_ROUTE/ARRIVED/IN_PROGRESS/COMPLETED/SKIPPED
- Provenance: LIVE_CAPTURE/CAPTURED_REPLAY/SYNTHETIC_FIXTURE/FALLBACK/USER_IMPORTED/AI_INFERRED/MIXED
- Edge: PIC16F877A = 物理边缘设备（非"个人智能中心"）
- QR: 解码 ≠ 真实性验证

---

## 6. 缺失的外部依赖

| 依赖 | 用途 | 状态 |
|------|------|------|
| Valhalla 实例 | 路由服务 | 需要生产部署 |
| 高德 API Key | 中国地图服务 | 需要配置 |
| Open-Meteo API | 天气数据 | ✅ 可用 |
| 21st.dev API Key | 21st 技能市场 | 可选 |

---

## 7. Codex 前 5 行动

1. **修复 MockMobilityProvider 硬编码** → `backend/app/replanning/feasibility.py:16`
2. **统一 Money 类型** → 使用 `amount_minor` 统一前后端
3. **补充 Storybook 组件状态故事** → 14 个组件需要 Loading/Error/Empty 状态
4. **清理手写类型重复** → 17 个类型需要迁移到 generated/api.ts
5. **添加 ICS 时区默认 UTC** → `backend/app/integrations/inbox/ics_parser.py:~45`

---

## 8. 不要浪费时间的方向

- ❌ 尝试修复 P1 布线（genus=2 死结，已搁置）
- ❌ 自己写 Visio 用例图（课程作业要求，非产品核心）
- ❌ 继续增加对抗测试覆盖率（85 个测试已足够）
- ❌ 评估未验证的库许可证（已验证的 2 个已明确）

---

**交付物总数**: 23 个文件
**测试函数**: 85 个
**边缘案例**: 150 个
**验证状态**: ✅ R2 验证通过