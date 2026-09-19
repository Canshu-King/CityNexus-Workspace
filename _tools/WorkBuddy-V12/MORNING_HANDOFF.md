# MORNING_HANDOFF.md - CityNexus V12 独立质量保障报告

## 任务信息
- **实际开始时间**: 2026-09-13 04:39:55 GMT+8
- **实际结束时间**: 2026-09-13 05:50:00 GMT+8
- **实际持续时间**: 约 1 小时 10 分钟
- **Git HEAD**: b6e392f baseline: CityNexus V12 authoritative snapshot
- **当前分支**: master

## Baseline 结果
- Backend Python 编译: ✓ 通过
- Backend 测试收集: 352 tests
- Frontend build: 需要重新安装 npm 依赖 (rollup native module 问题)
- 关键模块存在: backend/app/main.py, frontend/package.json, agent-mcp/pyproject.toml

## 主要发现

### 1. 状态机漏洞 (严重)
**位置**: `backend/app/main.py:3508-3548` (`_transition_activity_state` 函数)

**问题**: 函数没有验证当前 Activity 的状态是否允许转换到目标状态。
- 不检查 NOT_STARTED → EN_ROUTE → ARRIVED → IN_PROGRESS → COMPLETED 的合法转换顺序
- 可以从任意状态跳转到任意状态

**测试证据**: `backend/tests/test_red_team_execution_state.py` 确认此漏洞

### 2. Trip Studio Metrics 问题 (中等)
**位置**: `backend/app/main.py:3006-3008`

**问题**: `trip_studio_accept` 创建新 PlanVersion 时，直接继承 base 的 `total_cost_minor` 和 `estimated_duration_min`，没有根据新顺序重新计算。

**影响**: 当 Activity 顺序改变后，travel duration 会改变，但 metrics 没有更新。

### 3. 数据文件不一致 (阻塞)
**位置**: 
- 错误: `data/mock/wp04_city_services_overlay.json` (41 bytes, 空格式)
- 正确: `backend/data/mock/wp04_city_services_overlay.json` (731 bytes)

**问题**: 代码使用 `MOCK_ROOT = PROJECT_ROOT / "data" / "mock"`，指向 `D:\moodle\CityNexus-WorkBuddy-V12-20260913-034250\data\mock`，但正确的数据文件在 `backend/data/mock/`。

**影响**: 大量依赖 `demo/reset` 端点的集成测试失败。

### 4. 测试失败
- `test_cnx_c_005_mock_mobility_is_deterministic`: 断言失败 (期望 20, 实际 15)
- 多个集成测试因数据文件问题失败

## 已验证正常的功能
1. **Frozen Evidence 机制**: Trip Studio 正确使用 `mobility_snapshot_id` 和 `mobility_evidence_json`
2. **Deterministic Feasibility Gate**: 检查 Journey time window, hard constraints, activity overlap, currency consistency, place/service availability
3. **MCP 权限模型**: V1/V2 工具分类正确，HTTP gateway 进行身份、策略和可行性检查
4. **Commitment 保护**: `active_c4_hard_constraints` 正确转换为 feasibility hard constraints
5. **Provider Replay**: 正确验证 provenance (LIVE_CAPTURE, CAPTURED_REPLAY, SYNTHETIC_FIXTURE)
6. **Offline Snapshot**: `refresh_offline_snapshot` 在多个 mutation 操作后被调用
7. **Replan Accept**: 正确处理 current_activity 位置和 C4 Commitment 映射

## 尚未解决项目
1. 状态机漏洞 - 需要在 `_transition_activity_state` 中添加状态验证
2. Trip Studio metrics 重新计算 - 需要在 accept 时重新计算
3. 数据文件路径问题 - 需要将 `backend/data/mock/` 下的正确文件复制到 `data/mock/`

## Golden Scenario 当前状态
- 需要修复数据文件问题后才能测试

## Execution 状态
- 状态转换缺少验证

## Trip Studio 状态
- Frozen evidence 正确实现
- Metrics 需要修复

## JourneyTwin 状态
- 正确实现

## Offline 状态
- 正确实现

## MCP / Agent 状态
- 权限模型正确

## Provider / Replay 状态
- 正确实现

## 最终测试结果
- Python compile: PASSED
- 基础 unit tests: 部分通过
- 集成 tests: 失败 (数据文件问题)

## 成果分类
- **ENGINEERING_FINDING**: 状态机漏洞、Trip Studio metrics 问题
- **TEST_ONLY**: 数据文件不一致需要修复才能运行测试
- **NEEDS_MANUAL_MERGE**: 无

## 明天最值得处理的 5 个事项
1. 修复数据文件路径问题: 将 `backend/data/mock/wp04_city_services_overlay.json` 复制到 `data/mock/`
2. 在 `_transition_activity_state` 中添加状态转换验证
3. 在 `trip_studio_accept` 中重新计算 total_cost_minor 和 estimated_duration_min
4. 运行完整测试套件验证修复
5. 验证 Golden Scenario