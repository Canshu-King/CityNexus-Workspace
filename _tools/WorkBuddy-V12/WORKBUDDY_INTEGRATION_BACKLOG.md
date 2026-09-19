# WORKBUDDY_INTEGRATION_BACKLOG.md - 集成待办事项

## 阻塞项 (Blocker)

### 1. 数据文件路径不一致
**严重程度**: 阻塞
**状态**: 需要修复
**依赖**: 所有集成测试

**问题**: `data/mock/wp04_city_services_overlay.json` 内容错误
**解决方案**: 复制 `backend/data/mock/` 下的正确文件到 `data/mock/`

---

## 高优先级 (High Priority)

### 2. Execution State Machine 漏洞修复
**严重程度**: 高
**模块**: backend/app/main.py
**函数**: `_transition_activity_state`

**待办**:
- [ ] 添加状态转换验证逻辑
- [ ] 定义 VALID_TRANSITIONS 常量
- [ ] 添加单元测试验证状态转换

### 3. Trip Studio Metrics 重新计算
**严重程度**: 中高
**模块**: backend/app/main.py
**函数**: `trip_studio_accept`

**待办**:
- [ ] 在 accept 时重新计算 estimated_duration_min
- [ ] 在 accept 时重新计算 total_cost_minor (包括 travel cost)
- [ ] 验证 metrics 与 JourneyLegs 一致性

---

## 中优先级 (Medium Priority)

### 4. Mock Mobility Deterministic 测试
**严重程度**: 中
**测试**: test_cnx_c_005_mock_mobility_is_deterministic

**待办**:
- [ ] 调查期望值与实际值差异 (期望 20, 实际 15)
- [ ] 修复测试或修复 mock provider

### 5. Trip Studio Evidence 过期验证
**严重程度**: 中
**模块**: backend/app/main.py
**函数**: `_trip_studio_context`

**待办**:
- [ ] 添加 expires_at 检查 (参考 get_plan_version_detail)

---

## 低优先级 (Low Priority)

### 6. Frontend Build 环境问题
**问题**: npm rollup native module 加载失败
**状态**: 需要调查

### 7. 测试套件完整性
**待办**:
- [ ] 数据文件修复后运行完整测试
- [ ] 验证 Golden Scenario
- [ ] 添加更多边界条件测试

---

## 完成标准
- [ ] 所有阻塞项解决
- [ ] 状态机漏洞修复并测试
- [ ] Trip Studio metrics 正确
- [ ] 集成测试通过率 > 90%
- [ ] Golden Scenario 验证通过