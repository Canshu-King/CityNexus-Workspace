# WORKBUDDY_TEST_REPORT.md - CityNexus V12 测试报告

## 测试执行摘要

**执行时间**: 2026-09-13 04:39:55 - 05:50:00 GMT+8
**测试环境**: Python 3.13.12, pytest 9.1.1
**总测试数**: 352 tests (collected)

## 测试结果

### 通过的测试
| 测试文件 | 结果 | 说明 |
|---------|------|------|
| test_contract.py | 3/4 passed | 1 failed: mock mobility deterministic |
| test_foundation_registry.py | 2/2 passed | |
| test_foundation_planner_adapter.py | 1/1 passed | |
| test_foundation_routingpy_adapter.py | 1/1 passed | |
| test_foundation_discovery_pipeline.py | 1/1 passed | |
| test_foundation_http_adapters.py | 3/3 passed | |
| test_foundation_opportunity_window.py | 1/1 passed | |
| test_foundation_reason_codes.py | 2/2 passed | |
| test_foundation_replan_diff.py | 1/1 passed | |
| test_red_team_execution_state.py | 3/3 passed | 代码审查确认漏洞 |

### 失败的测试
| 测试文件 | 失败数 | 原因 |
|---------|--------|------|
| test_contract.py | 1 | mock mobility 期望值不匹配 |
| test_agent_principal_boundary.py | 2 | 数据文件问题 |
| test_agent_alternatives_v3.py | 1 | 数据文件问题 |
| test_gpt_adversarial_provider_hardening.py | 4 | 数据文件问题 |
| test_agent_runtime_gate.py | 18 | 数据文件问题 |

## 失败分析

### 1. test_cnx_c_005_mock_mobility_is_deterministic
```
AssertionError: assert 15 == 20
```
**原因**: Mock provider 返回的 estimate_minutes 值与测试期望不一致。

### 2. 数据文件问题导致的失败
**根本原因**: `data/mock/wp04_city_services_overlay.json` 内容为空/错误
**影响**: 所有依赖 `demo/reset` 端点的测试失败

错误信息:
```
TypeError: string indices must be integers, not 'str'
  at app/services.py:220
```

## 测试覆盖率

### 已覆盖模块
- ✅ Foundation registry
- ✅ Planner adapter
- ✅ Routing adapter
- ✅ Discovery pipeline
- ✅ HTTP adapters
- ✅ Opportunity window
- ✅ Reason codes
- ✅ Replan diff
- ✅ Execution state machine (red team)

### 未覆盖模块 (因数据问题)
- ❌ Agent runtime gate
- ❌ Agent alternatives
- ❌ Adversarial provider hardening
- ❌ Backend connected golden contract
- ❌ Trip Studio execution
- ❌ Replanning feasibility

## 建议

1. **立即修复**: 数据文件路径问题 - 将 `backend/data/mock/` 下的文件复制到 `data/mock/`
2. **调查修复**: mock mobility deterministic 测试
3. **后续测试**: 数据文件修复后运行完整测试套件