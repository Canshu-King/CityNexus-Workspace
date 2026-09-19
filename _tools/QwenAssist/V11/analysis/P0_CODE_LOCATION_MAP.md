# CityNexus V11 — P0 代码位置映射

**生成时间**: 2026-09-12 23:45  
**分析范围**: `D:\moodle\CityNexus\backend\app`, `frontend\src`, `agent-mcp`  
**用途**: 为 Codex 提供精确的代码位置索引，节省定位时间

---

## 1. Real DeepSeek V4.1 Live CityNexus Tool Loop

**核心文件**:
- `backend/app/agent/orchestrator.py` (L18-62) — HermesJourneyAgent 适配器，优先使用 Hermes 运行时
- `backend/app/agent/runtime.py` — DeepSeekJourneyAgent 原生实现（需读取确认完整循环）
- `backend/app/main.py` — FastAPI 入口，注册 agent 路由

**当前行为**:
- `configured_journey_agent()` 函数检查 `settings.hermes_api_url` 和 `hermes_api_key`
- 若 Hermes 可用则返回 `HermesJourneyAgent`（OpenAI 兼容协议）
- 否则回退到原生 `DeepSeekJourneyAgent`

**Gap**:
- Hermes 是外部运行时，非 DeepSeek V4.1 原生
- 需要确认 `runtime.py` 中的原生 DeepSeek 循环是否完整实现 tool_call → tool_output → continue 循环

**最小实现路径**:
1. 读取 `backend/app/agent/runtime.py` 确认 `DeepSeekJourneyAgent.run()` 方法
2. 验证是否处理 `tool_calls` → `function_call_output` → 继续生成
3. 若缺失，补充循环逻辑直到 `max_steps` 或模型返回 `FINISH`

**依赖测试**:
- `backend/tests/test_agent_mission_runtime.py`
- `backend/tests/test_v10_flagship_e2e.py`

---

## 2. Generic Compose Still Using MockMobilityProvider

**核心文件**:
- `backend/app/replanning/feasibility.py` (L16) — 导入 `MockMobilityProvider`
- `backend/app/integrations/mock/providers.py` (L22-67) — `MockMobilityProvider` 定义
- `backend/app/integrations/mobility/runtime.py` — 真实移动性提供者运行时

**当前行为**:
- `FeasibilityContext` (L38-52) 接收 `mobility_provider: Any`
- 调用 `_field(constraint, "params", {})` 解析约束
- 使用 `mobility_provider.estimate()` 计算行程时间

**Gap**:
- Feasibility gate 仍硬编码导入 `MockMobilityProvider`
- 真实提供者（Valhalla/高德）未完全接入选择门

**最小实现路径**:
1. 将 `MockMobilityProvider` 改为依赖注入（从 `Context` 传入）
2. 在 `main.py` 或 `services.py` 中配置真实提供者
3. 更新测试以同时覆盖 mock 和真实提供者

**依赖测试**:
- `backend/tests/test_provider_runtime_gate.py`
- `backend/tests/test_vertical_slice_hardening_next.py`

---

## 3. Plan Selection Final Gate Using Different Mobility Truth

**核心文件**:
- `backend/app/planning/solver_contract.py` — 求解器契约定义
- `backend/app/planning/solver_v2.py` — 求解器实现
- `backend/app/replanning/feasibility.py` — 可行性门

**当前行为**:
- `solver_v2.py` 生成候选方案
- `feasibility.py` 执行确定性检查
- 两者可能使用不同的移动性数据源

**Gap**:
- 需要验证求解器和可行性门是否使用相同的 `mobility_provider` 实例
- 若求解器使用快照而门使用实时数据，会导致不一致

**最小实现路径**:
1. 在 `solver_contract.py` 中明确要求 `mobility_provider` 参数
2. 确保 `solver_v2.py` 和 `feasibility.py` 共享同一实例
3. 添加测试验证一致性

---

## 4. OpenAPI Generated TS Types Not Actually Driving Client Types

**核心文件**:
- `contracts/` — OpenAPI schema 定义
- `frontend/src/` — TypeScript 客户端代码
- `frontend/src/types/` 或 `frontend/src/lib/types.ts` — 手动类型定义

**当前行为**:
- 后端 OpenAPI schema 自动生成（可能使用 FastAPI 的 `/openapi.json`）
- 前端可能有手动声明的接口

**Gap**:
- 前端类型未从 OpenAPI 自动生成
- 存在类型漂移风险

**最小实现路径**:
1. 使用 `openapi-typescript` 或 `oazapfts` 从 `/openapi.json` 生成类型
2. 替换前端手动类型或建立同步机制
3. 在 CI 中添加类型校验

**依赖**:
- TRACK D 详细审计见 `frontend/OPENAPI_TYPE_ADOPTION_PLAN.md`

---

## 5. Leg-Level Provider Provenance

**核心文件**:
- `backend/app/integrations/provider_config.py` — 提供者配置
- `backend/app/integrations/registry.py` — 提供者注册表
- `backend/app/db/models.py` — 数据模型（需确认是否有 `provenance` 字段）

**当前行为**:
- 每个提供者有 `provider_key` 属性
- `TravelEstimate` (L7) 包含 `provider_key: str`

**Gap**:
- 需要追踪每条腿（leg）的来源提供者
- 混合来源（如部分 Valhalla、部分高德）的行程需要标记为 `MIXED`

**最小实现路径**:
1. 在 `JourneyLeg` 模型中添加 `provenance: str` 字段
2. 在聚合时检测多提供者并标记 `MIXED`
3. 前端显示来源标识

**依赖测试**:
- TRACK I 的 `providers/PROVENANCE_TEST_MATRIX.csv`

---

## 6. UNKNOWN Money Semantics

**核心文件**:
- `backend/app/stay_mobility.py` — 住宿和移动性逻辑
- `backend/app/integrations/commerce_ports.py` — 商业接口
- `backend/app/db/models.py` — 价格字段定义

**当前行为**:
- 价格可能有 `UNKNOWN`、`ESTIMATED`、`KNOWN` 状态
- 需要确认货币处理逻辑

**Gap**:
- `UNKNOWN` 价格不应视为免费
- 外币应保持原币种显示
- 取消损失 `UNKNOWN` 不应自动执行

**最小实现路径**:
1. 在 `Money` 或 `Price` 类中明确状态枚举
2. 添加验证逻辑阻止 `UNKNOWN` → `FREE` 的隐式转换
3. 前端显示价格状态标识

**依赖测试**:
- TRACK B3 的金钱语义测试

---

## 7. ExecutionClock / Edge Countdown / Offline Actual-Now

**核心文件**:
- `backend/app/execution/traveler_twin.py` — 旅行者数字孪生
- `backend/app/execution/` — 执行相关模块
- `backend/app/integrations/edge/` — Edge 设备集成（如有）

**当前行为**:
- 需要确认当前时间获取逻辑
- 离线模式下的 `actual-now` 处理

**Gap**:
- Edge 倒计时逻辑
- 离线时 `actual-now` 可能使用设备时间而非服务器时间

**最小实现路径**:
1. 统一时间源（服务器 NTP 同步）
2. 离线时使用最后已知服务器时间 + 设备偏移
3. Edge 倒计时显示在 UI

---

## 8. MapLibre Resize

**核心文件**:
- `frontend/src/components/Map*.tsx` — MapLibre 组件
- `frontend/src/styles/` — 样式文件

**当前行为**:
- MapLibre 在容器大小变化时可能未正确重绘

**Gap**:
- 需要添加 `resizeObserver` 或窗口 `resize` 事件监听
- 调用 `map.resize()` 或 `map.triggerRepaint()`

**最小实现路径**:
1. 在 Map 组件中添加 `useEffect` 监听容器尺寸
2. 调用 `map.resize()` 方法
3. 测试移动端横竖屏切换

---

## 9. Storybook State Coverage

**核心文件**:
- `frontend/.storybook/` — Storybook 配置
- `frontend/src/**/*.stories.tsx` — 组件故事

**当前行为**:
- 需要盘点现有故事覆盖的状态

**Gap**:
- 许多组件缺少 `loading`、`empty`、`error`、`offline`、`stale`、`risk`、`protected`、`disabled` 状态

**最小实现路径**:
1. 为每个核心组件补充状态故事
2. 使用 `frontend/STORYBOOK_MATRIX.csv` 追踪进度
3. 在 CI 中运行 Storybook 视觉回归测试

---

## 10. Sourceful Web Evidence

**核心文件**:
- `backend/app/integrations/ai/web_research.py` — 网络研究
- `backend/app/integrations/ai/responses.py` — DeepSeek Responses API
- `web/` — Web 搜索相关模块

**当前行为**:
- DeepSeek 内置网络搜索
- 需要评估 SearXNG 作为可选提供者

**Gap**:
- 搜索结果需要来源分类（官方/SEO/社交/缓存）
- 需要处理页面内提示注入

**最小实现路径**:
1. 实现 `WebObservation` 数据结构
2. 添加来源分类器
3. 生成对抗性测试用例（TRACK H）

---

## 下一步行动（Codex 优先执行）

1. **读取 `backend/app/agent/runtime.py`** — 确认 DeepSeek 原生循环完整性
2. **审计 `frontend/src/types/`** — 列出所有手动类型并与 OpenAPI 对比
3. **检查 `backend/app/db/models.py`** — 确认 `JourneyLeg` 是否有 `provenance` 字段
4. **补充 Storybook 故事** — 从 `ActivityCard` 和 `JourneyLeg` 开始
5. **修复 MapLibre resize** — 添加 `ResizeObserver`

---

**备注**: 本映射基于快速扫描生成，部分细节需读取完整文件确认。
