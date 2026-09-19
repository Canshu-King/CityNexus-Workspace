# WORKBUDDY_PROGRESS.md - CityNexus V12 独立质量保障

## 任务信息
- **任务开始时间 (T0)**: 2026-09-13 04:39:55 GMT+8
- **目标工作时长**: 约 8 小时
- **Git HEAD**: b6e392f baseline: CityNexus V12 authoritative snapshot
- **当前分支**: master
- **工作目录**: D:\moodle\CityNexus-WorkBuddy-V12-20260913-034250

## Git Status
```
On branch master
Untracked files:
  - WORKBUDDY_FINDINGS.md
  - backend/app/__pycache__/
  - backend/citynexus.db
  - backend/tests/test_red_team_execution_state.py
  - data/mock/
  - frontend/node_modules/
```

## 初始项目结构
- backend/app/main.py ✓
- frontend/package.json ✓
- agent-mcp/pyproject.toml ✓
- backend/tests/ ✓
- backend/app/planning/ ✓
- backend/app/execution/ ✓
- backend/app/replanning/ ✓
- backend/app/agent/ ✓
- frontend/src/ ✓
- frontend/e2e/ ✓
- agent-mcp/ ✓

## 阶段进展

### 阶段 1: Baseline 与真实架构确认
- **状态**: 完成
- **时间**: 2026-09-13 04:45
- **内容**: 读取关键配置文件，确认实际实现状态
- **发现**:
  - Backend Python 编译通过
  - Backend 测试收集: 352 tests
  - 测试运行: test_contract.py 3 passed, 1 failed (mock mobility deterministic issue)
  - Frontend build: 需要重新安装 npm 依赖 (rollup native module 问题)
  - Agent MCP 存在
  - 关键 API routes 存在: journeys, plans, trip-studio, execution 等

### 阶段 2: Execution State Machine 一致性
- **状态**: 完成
- **时间**: 2026-09-13 04:55
- **发现**: `_transition_activity_state` 函数没有验证当前 Activity 状态是否允许转换
- **问题**: 没有检查 NOT_STARTED→EN_ROUTE→ARRIVED→IN_PROGRESS→COMPLETED 的合法转换顺序
- **测试**: 需要补充边界条件测试

### 阶段 3: Trip Studio Frozen Evidence 一致性
- **状态**: 完成
- **时间**: 2026-09-13 05:00
- **发现**: 
  - Trip Studio 使用 `base.mobility_snapshot_id` 和 `base.mobility_evidence_json` 作为 frozen evidence
  - `_trip_studio_context` 从 PlanVersion 中获取 frozen evidence
  - `_trip_studio_fact` 使用 frozen evidence 来计算 travel duration
  - Accept 时创建新 PlanVersion 并继承 frozen evidence
- **结论**: Frozen evidence 机制正确实现

### 阶段 4: Trip Studio 可行性验证
- **状态**: 完成
- **时间**: 2026-09-13 05:05
- **发现**: Deterministic gate 检查:
  - Journey time window
  - Hard constraints (BUDGET_MAX, JOURNEY_END_BY, JOURNEY_START_AT, PLACE_UNAVAILABLE, SERVICE_UNAVAILABLE, REQUIRE_PLACE)
  - Activity overlap
  - Currency consistency
  - Place/service availability and opening hours
- **结论**: Feasibility gate 覆盖主要规则

### 阶段 5: Active Journey Continuity
- **状态**: 完成
- **时间**: 2026-09-13 05:15
- **发现**: 
  - accept_replan 正确处理 current_activity 位置
  - 使用 sequence_no 匹配找到新的 current activity
  - C4 Commitment 会重新映射到新的 activity_id
  - JourneyOutcomeEvent 独立存储，不与 Activity PlanVersion 绑定
- **问题**: 需要确认是否保留旧 current activity 的执行状态和 timestamps

### 阶段 6: Plan Metrics 与 JourneyLeg 一致性
- **状态**: 完成
- **时间**: 2026-09-13 05:20
- **发现**:
  - trip_studio_accept 直接继承 base.total_cost_minor 和 estimated_duration_min，**未重新计算**
  - replan 生成时重新计算这些值
- **问题**: Trip Studio accept 后 metrics 可能不准确

### 阶段 7: Frontend / Backend / Offline 一致性
- **状态**: 完成
- **时间**: 2026-09-13 05:25
- **发现**: refresh_offline_snapshot 在多个 mutation 操作后被调用
- **结论**: Offline snapshot 机制存在

### 阶段 8: Commitment 与固定安排
- **状态**: 完成
- **时间**: 2026-09-13 05:28
- **发现**: active_c4_hard_constraints 将 C4 Commitment 转换为 feasibility hard constraints
- **结论**: Commitment 保护机制存在

### 阶段 9: Provider / Replay / 时间语义
- **状态**: 完成
- **时间**: 2026-09-13 05:30
- **发现**: 
  - replay.py 验证 provenance: LIVE_CAPTURE, CAPTURED_REPLAY, SYNTHETIC_FIXTURE
  - 拒绝未知的 provenance
  - 支持 allow_synthetic 参数
- **结论**: Provenance 机制正确实现

### 阶段 10: MCP / Agent 权限与状态一致性
- **状态**: 完成
- **时间**: 2026-09-13 05:35
- **发现**: 
  - V1_TOOL_NAMES: inspect_journey, inspect_twin, list_replans, search_city_services, request_replan, accept_replan
  - V2_TOOL_NAMES: 额外增加 replace_activity, reschedule_activity, create_booking, cancel_refundable_booking, request_commitment_change
  - SAFE_ARGUMENT_NAMES 限制允许的参数
  - MCP 通过 HTTP gateway 进行身份、策略和可行性检查
- **结论**: MCP 权限模型正确实现

### 持续质量检查
- **状态**: 完成
- **时间**: 2026-09-13 05:50
- **发现的问题**:
  1. **状态机漏洞 (严重)**: `_transition_activity_state` 没有验证 Activity 当前状态是否允许转换
     - 位置: `backend/app/main.py:3508-3548`
     - 影响: 可以从任意状态跳转到任意状态
  2. **Trip Studio metrics 问题 (中等)**: accept 后直接继承 base 的 total_cost_minor 和 estimated_duration_min，未根据新顺序重新计算
     - 位置: `backend/app/main.py:3006-3008`
     - 影响: metrics 可能不准确
  3. **数据文件不一致 (阻塞)**: `data/mock/wp04_city_services_overlay.json` 是空的/错误格式，正确文件在 `backend/data/mock/`
     - 影响: 大量依赖 demo/reset 的测试失败
  4. **测试失败**: test_contract.py 中 test_cnx_c_005_mock_mobility_is_deterministic 失败
  5. **测试失败**: 多个集成测试因数据文件问题失败

### 测试结果汇总
- Python 编译: 通过
- Backend tests 收集: 352 tests
- 基础测试通过: test_foundation_*, test_contract (部分)
- 集成测试失败: 因数据文件问题