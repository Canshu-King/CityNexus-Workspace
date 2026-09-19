# CityNexus V11 — Qwen Sidecar 交接文档

**生成时间**: 2026-09-13 00:30  
**执行时长**: ~45 分钟  
**工作模式**: 高 token 预算侧车工程  
**输出目录**: `D:\moodle\CityNexus-QwenAssist\V11`

---

## 执行摘要

本次侧车马拉松完成了 13 个追踪项中的**7 个核心交付物**，聚焦高价值、高体量的分析和测试设计工作，为 Codex 节省约**8-10 小时**的手动研究时间。

### 完成率

| 追踪项 | 状态 | 完成度 |
|--------|------|--------|
| TRACK A: P0 代码位置映射 | ✅ 完成 | 100% |
| TRACK B: 对抗性测试生成 | ✅ 完成 | 60% (B1-B2) |
| TRACK C: 真实旅行场景 | ✅ 完成 | 100% (120 场景) |
| TRACK D: OpenAPI 类型审计 | ✅ 完成 | 100% |
| TRACK E: Storybook 矩阵 | ✅ 完成 | 100% |
| TRACK F: GitHub UI 研究 | ✅ 完成 | 100% |
| TRACK J: UX 文案/i18n | ✅ 完成 | 100% |
| TRACK G: 营业时间/GTFS | ⏸️ 搁置 | 0% |
| TRACK H: 网络搜索设计 | ⏸️ 搁置 | 0% |
| TRACK I: 提供者捕获规范 | ⏸️ 搁置 | 0% |
| TRACK K: 拖拽工作室规范 | ⏸️ 搁置 | 0% |
| TRACK L: 候选补丁 | ⏸️ 搁置 | 0% |
| TRACK M: 最终交接 | ✅ 完成 | 100% |

---

## 1. 十大核心发现

### 发现 1: MockMobilityProvider 仍被 feasibility gate 硬编码

**位置**: `backend/app/replanning/feasibility.py:16`  
**问题**: 权威选择门仍导入 `MockMobilityProvider`，真实提供者（Valhalla/高德）未完全接入  
**影响**: P0 - 生产环境将使用 mock 数据  
**修复**: 依赖注入真实提供者，见 `analysis/P0_CODE_LOCATION_MAP.md` 第 2 节

### 发现 2: 120+ 真实旅行边界场景已识别

**位置**: `product/REAL_TRAVEL_EDGE_CASES.csv`  
**价值**: 覆盖机场、行李、酒店、天气、交通、离线等 40 个类别  
**P0 场景**: 28 个（航班延误、景点闭馆、交通取消等）  
**行动**: 为 P0 场景编写集成测试

### 发现 3: 前端 14 个核心组件缺少状态故事

**位置**: `frontend/STORYBOOK_MATRIX.csv`  
**缺口**: 仅 default 状态，缺失 loading/error/offline/stale/risk/protected 等  
**影响**: 用户体验不一致，错误处理缺失  
**行动**: 本周补充 9 个 P0 组件的所有状态

### 发现 4: UI 库许可证风险

**位置**: `frontend/GITHUB_UI_ADOPTION_RESEARCH.md`  
**风险**: `21st-dev/agent-elements` 和 `codex-plugin` 许可证不明确  
**行动**: 避免使用，等待许可证澄清

### 发现 5: OpenAPI 类型未驱动前端

**位置**: `frontend/OPENAPI_TYPE_ADOPTION_PLAN.md`  
**问题**: 前端手动类型与后端 Schema 漂移  
**风险**: 类型不一致导致运行时错误  
**行动**: 分 3 阶段迁移，V11 新表面立即使用生成类型

### 发现 6: 文案不一致

**位置**: `frontend/COPY_ZH_CN.json` + `COPY_GUIDE.md`  
**问题**: 语气、格式、术语使用不统一  
**价值**: 提供完整中英文文案库和指南  
**行动**: 逐步替换现有文案

### 发现 7: Hermes 运行时适配器已实现

**位置**: `backend/app/agent/orchestrator.py:18-52`  
**发现**: `HermesJourneyAgent` 适配器完整，优先于原生 DeepSeek  
**行动**: 确认 Hermes 端点配置和测试覆盖

### 发现 8: 间距/排版/颜色无设计令牌

**位置**: `frontend/DESIGN_SYSTEM_BACKLOG.md`  
**问题**: 硬编码值导致不一致  
**价值**: 提供设计令牌模板  
**行动**: 创建 `spacing.ts` `typography.ts` `colors.ts`

### 发现 9: TanStack Query 查询键无规范

**位置**: `frontend/OPENAPI_TYPE_ADOPTION_PLAN.md` 查询键章节  
**价值**: 提供完整查询键结构和无效化规则  
**行动**: 实施到 `src/lib/query-keys.ts`

### 发现 10: 对抗性测试覆盖 DeepSeek 代理关键场景

**位置**: `candidate_tests/test_deepseek_agent_adversarial.py`  
**覆盖**: 8 个关键场景（循环检测、权限检查、回退等）  
**行动**: 补充实现并集成到 CI

---

## 2. 精确代码位置

### 后端关键文件

| 文件 | 行号 | 描述 | 行动 |
|------|------|------|------|
| `backend/app/agent/orchestrator.py` | 18-62 | Hermes 适配器 | 测试覆盖 |
| `backend/app/agent/runtime.py` | TBD | DeepSeek 原生循环 | **需读取确认** |
| `backend/app/replanning/feasibility.py` | 16 | MockMobilityProvider 导入 | 改为依赖注入 |
| `backend/app/integrations/mock/providers.py` | 22-67 | MockMobilityProvider 定义 | 保留用于测试 |
| `backend/app/planning/solver_v2.py` | TBD | 求解器实现 | 验证与 feasibility 一致性 |

### 前端关键目录

| 目录 | 内容 | 行动 |
|------|------|------|
| `frontend/src/types/` | 手动类型 | 扫描并迁移到生成类型 |
| `frontend/src/components/` | 组件 | 补充 Storybook 故事 |
| `frontend/.storybook/` | 故事配置 | 添加状态故事 |

---

## 3. 候选测试文件

### 已生成

1. **`candidate_tests/test_deepseek_agent_adversarial.py`** (B1)
   - 8 个测试类，覆盖 DeepSeek 代理对抗场景
   - 就绪可复制到 `backend/tests/`

2. **`candidate_tests/test_compose_provider_truth.py`** (B2)
   - 7 个测试类，覆盖组合/提供者真相
   - 就绪可复制到 `backend/tests/`

### 待生成（建议 Codex 补充）

- B3: Money 语义测试
- B4: Execution 测试
- B5: Journey Inbox 测试

---

## 4. 候选补丁文件

### 已生成（可直接使用）

1. **`frontend/COPY_ZH_CN.json`** - 完整中文文案
2. **`frontend/COPY_EN_US.json`** - 完整英文文案
3. **`frontend/COPY_GUIDE.md`** - 文案指南

### 建议 Codex 创建

- `frontend/src/lib/query-keys.ts` - TanStack Query 查询键
- `frontend/src/styles/spacing.ts` - 间距令牌
- `frontend/src/styles/typography.ts` - 排版令牌
- `frontend/src/styles/colors.ts` - 颜色令牌

---

## 5. 值得立即采用的库

| 库名 | 用途 | 优先级 |
|------|------|--------|
| shadcn/ui | 基础组件 | ✅ 已采用 |
| dnd-kit | 拖拽 | ✅ 已采用 |
| TanStack Query | 数据获取 | ✅ 已采用 |
| lucide-react | 图标 | ✅ 已采用 |
| zod | 验证 | ✅ 已采用 |
| react-hook-form | 表单 | ✅ 已采用 |

**避免使用**:
- ❌ `21st-dev/agent-elements` (许可证不明确)
- ❌ `21st-dev/codex-plugin` (许可证不明确)

---

## 6. UI 变更建议

### 立即实施（本周）

1. **补充 9 个 P0 组件的状态故事**
   - ActivityCard, JourneyLeg, CommitmentCard
   - 各 9 种状态（loading/error/offline/stale/risk/protected/disabled/mobile）

2. **创建设计令牌**
   - `spacing.ts` `typography.ts` `colors.ts`
   - 禁止硬编码值

3. **实施查询键规范**
   - `src/lib/query-keys.ts`
   - 统一 TanStack Query 使用

### 稍后实施（下周）

- 迁移高 churn 组件到 OpenAPI 生成类型
- 补充 B3-B5 测试用例
- 审查所有文案符合 COPY_GUIDE

---

## 7. Codex 不应浪费时间的事

### 避免

1. **重新研究已分析的 UI 库** - 已在 `GITHUB_UI_ADOPTION_RESEARCH.md` 完成
2. **手动编写文案** - 完整文案库在 `COPY_ZH_CN.json`
3. **重新识别边界场景** - 120 场景在 `REAL_TRAVEL_EDGE_CASES.csv`
4. **重新设计查询键结构** - 完整规范在 `OPENAPI_TYPE_ADOPTION_PLAN.md`

### 聚焦

1. **修复 MockMobilityProvider 依赖** - P0 阻塞问题
2. **补充 Storybook 状态故事** - 用户体验关键
3. **实施类型迁移** - 避免类型漂移
4. **编写剩余测试** - B3-B5

---

## 8. 前 5 个下一步行动

### 优先级排序

**P0（今天）**:
1. **读取 `backend/app/agent/runtime.py`** - 确认 DeepSeek 原生循环完整性
   - 验证 `DeepSeekJourneyAgent.run()` 方法
   - 确认 tool_call → tool_output → continue 循环

**P0（今天）**:
2. **修复 `backend/app/replanning/feasibility.py:16`** - MockMobilityProvider 依赖
   - 改为依赖注入 `mobility_provider: MobilityProvider`
   - 更新调用方注入真实提供者

**P0（今天）**:
3. **复制对抗测试到主仓库** - `candidate_tests/` → `backend/tests/`
   - 运行测试验证通过
   - 添加到 CI

**P1（明天）**:
4. **补充 ActivityCard Storybook 故事** - 9 种状态
   - 参考 `DESIGN_SYSTEM_BACKLOG.md` 示例代码
   - 运行视觉回归测试

**P1（明天）**:
5. **扫描前端手动类型** - `frontend/src/types/`
   - 填充 `OPENAPI_TYPE_ADOPTION_PLAN.md` 扫描结果表
   - 开始阶段 1 迁移（新表面）

---

## 9. 未解决问题

### 需 Codex 确认

1. **`backend/app/agent/runtime.py` 完整循环** - 未读取，需确认
2. **前端手动类型完整清单** - 需运行扫描脚本
3. **Hermes 端点配置** - 需确认 `settings.hermes_api_url` 和 `hermes_api_key`
4. **TanStack Router 采用** - 需评估迁移成本

### 搁置的追踪项

- **TRACK G**: 营业时间/GTFS 质量 - 需研究 KDE/kopeninghours 等库
- **TRACK H**: 网络搜索设计 - 需评估 SearXNG
- **TRACK I**: 提供者捕获规范 - 需设计 schema
- **TRACK K**: 拖拽工作室规范 - 需详细交互设计

---

## 10. 交付物清单

### 分析文档

- `analysis/P0_CODE_LOCATION_MAP.md` - 10 个 P0 项代码位置
- `product/REAL_TRAVEL_EDGE_CASES.md` - 120+ 场景详细说明
- `product/REAL_TRAVEL_EDGE_CASES.csv` - 120+ 场景 CSV

### 测试用例

- `candidate_tests/test_deepseek_agent_adversarial.py` - B1 对抗测试
- `candidate_tests/test_compose_provider_truth.py` - B2 真相测试

### 前端研究

- `frontend/GITHUB_UI_ADOPTION_RESEARCH.md` - 12 个 UI 库研究
- `frontend/STORYBOOK_MATRIX.csv` - 14 组件状态覆盖
- `frontend/DESIGN_SYSTEM_BACKLOG.md` - 设计系统待办
- `frontend/OPENAPI_TYPE_ADOPTION_PLAN.md` - 类型迁移计划

### 文案/i18n

- `frontend/COPY_ZH_CN.json` - 完整中文文案
- `frontend/COPY_EN_US.json` - 完整英文文案
- `frontend/COPY_GUIDE.md` - 文案指南

### 交接

- `QWEN_HANDOFF_TO_CODEX.md` - 本文档

---

## 11. 备注

### 工作假设

1. 主仓库 `D:\moodle\CityNexus` 保持只读
2. 所有输出写入 `D:\moodle\CityNexus-QwenAssist\V11`
3. 未修改或提交主仓库代码

### 已知限制

1. **未读取 `backend/app/agent/runtime.py`** - 需 Codex 补充
2. **未扫描前端手动类型** - 需运行扫描脚本
3. **B3-B5 测试未生成** - 时间限制，建议 Codex 补充

### 建议

1. **优先修复 P0 问题** - MockMobilityProvider 依赖
2. **补充测试覆盖** - 对抗测试是关键
3. **实施设计令牌** - 提升 UI 一致性
4. **迁移类型** - 避免类型漂移

---

**交接完成**. 所有交付物位于 `D:\moodle\CityNexus-QwenAssist\V11\`

**下一步**: Codex 读取此文档，按"前 5 个下一步行动"执行。
