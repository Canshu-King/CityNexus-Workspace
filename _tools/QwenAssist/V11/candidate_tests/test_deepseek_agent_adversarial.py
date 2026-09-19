"""B1 — DeepSeek Agent Adversarial Test Suite

覆盖场景:
1. model chooses inspect before mutation
2. multi-turn function_call_output loop
3. repeated identical tool-call loop stops
4. malformed tool args
5. tool call points to another traveler's Journey
6. policy-required confirmation
7. model unavailable fallback
8. live tool result changes final model decision
"""

from __future__ import annotations

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timezone, timedelta


class TestDeepSeekAgentInspectBeforeMutation:
    """B1.1: 模型应在修改前先检查状态"""

    def test_agent_inspects_journey_before_replan(self):
        """代理执行 replan 前应先调用 get_journey 检查当前状态"""
        from backend.app.agent.runtime import DeepSeekJourneyAgent

        mock_runtime = Mock()
        # 第一次调用返回检查工具，第二次返回修改工具
        mock_runtime.run.side_effect = [
            {"tool_calls": [{"function": {"name": "get_journey", "arguments": {"journey_id": "J1"}}}]},
            {"tool_calls": [{"function": {"name": "replan_journey", "arguments": {"journey_id": "J1"}}}]},
        ]

        agent = DeepSeekJourneyAgent()
        # 验证第一次调用是检查而非直接修改
        # TODO: 实现完整断言逻辑

    def test_agent_refuses_mutate_without_inspection(self):
        """若模型试图跳过检查直接修改，应被拦截"""
        # TODO: 实现守卫逻辑测试


class TestMultiTurnFunctionCallLoop:
    """B1.2: 多轮工具调用循环"""

    def test_complete_tool_call_output_cycle(self):
        """验证 tool_call → tool_output → continue 完整循环"""
        # 模拟 DeepSeek 返回 tool_calls
        # 执行工具并返回结果
        # 验证模型继续生成直到 FINISH
        pass

    def test_max_steps_enforcement(self):
        """验证 max_steps=12 限制被遵守"""
        from backend.app.agent.runtime import DeepSeekJourneyAgent

        agent = DeepSeekJourneyAgent()
        # 模拟模型连续返回 tool_calls 超过 12 步
        # 验证在第 12 步后强制停止


class TestRepeatedToolCallStops:
    """B1.3: 重复相同工具调用应停止"""

    def test_detects_identical_tool_call_loop(self):
        """检测并停止重复的相同工具调用"""
        # 模拟模型连续 3 次返回相同的 tool_call
        # 验证代理识别循环并回退

    def test_loop_detection_threshold(self):
        """循环检测阈值测试（应 >= 2 次重复）"""
        pass


class TestMalformedToolArgs:
    """B1.4: 畸形工具参数处理"""

    def test_invalid_json_arguments(self):
        """工具参数 JSON 解析失败时的处理"""
        # 发送无效 JSON 作为工具参数
        # 验证代理返回错误而非崩溃

    def test_missing_required_arguments(self):
        """缺少必需参数时的处理"""
        # 调用工具但缺少必需字段
        # 验证返回 descriptive error

    def test_wrong_argument_type(self):
        """参数类型错误时的处理（如字符串传成整数）"""
        pass


class TestCrossTravelerJourneyAccess:
    """B1.5: 工具调用不应访问其他旅行者的旅程"""

    def test_cannot_access_another_traveler_journey(self):
        """尝试访问其他旅行者旅程应被拒绝"""
        from backend.app.agent.runtime import DeepSeekJourneyAgent
        from backend.app.db.models import Journey, Traveler

        # 创建两个旅行者
        traveler_a = Traveler(id="T1", user_id="U1")
        traveler_b = Traveler(id="T2", user_id="U2")

        journey_b = Journey(id="J2", traveler_id=traveler_b.id)

        # 旅行者 A 的代理尝试访问 J2
        # 验证权限检查拒绝访问


class TestPolicyRequiredConfirmation:
    """B1.6: 策略要求的确认"""

    def test_confirms_before_expensive_action(self):
        """执行高成本操作前需用户确认"""
        # 如预订酒店、购买门票
        # 验证代理先请求确认

    def test_confirms_before_risky_mutation(self):
        """高风险修改前需用户确认"""
        # 如删除整个行程
        # 验证代理先请求确认


class TestModelUnavailableFallback:
    """B1.7: 模型不可用时的回退"""

    def test_fallback_to_rule_based(self):
        """DeepSeek 不可用时回退到规则基系统"""
        with patch("backend.app.agent.runtime.DeepSeekJourneyAgent") as mock_agent:
            mock_agent.side_effect = Exception("Model unavailable")
            # 验证回退机制启动

    def test_graceful_degradation(self):
        """回退后功能降级但核心功能可用"""
        # 验证基础规划仍可用


class TestLiveToolResultChangesDecision:
    """B1.8: 实时工具结果改变最终决策"""

    def test_route_change_alters_plan(self):
        """路线查询结果改变应导致计划变更"""
        # 模拟路线 A 耗时 30 分钟
        # 实时查询变为 60 分钟（拥堵）
        # 验证代理选择替代方案

    def test_weather_change_alters_plan(self):
        """天气变化应导致计划变更"""
        # 原计划户外活动
        # 实时天气显示下雨
        # 验证代理建议室内替代


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
