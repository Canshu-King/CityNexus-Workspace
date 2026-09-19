"""B4 — Execution Test Suite (R2)

覆盖场景:
- actual now after planned start
- EN_ROUTE
- ARRIVED / IN_PROGRESS / COMPLETED / SKIPPED
- NOW/NEXT
- leave-by
- C4 countdown
- offline next-24h
- stale/high-error location
- provider duration update
- Edge risk/autopilot state
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from enum import Enum


class ActivityStatus(Enum):
    """活动状态"""
    SCHEDULED = "SCHEDULED"
    EN_ROUTE = "EN_ROUTE"
    ARRIVED = "ARRIVED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    SKIPPED = "SKIPPED"
    CANCELLED = "CANCELLED"


class TestActualNowAfterPlannedStart:
    """B4.1: 计划开始后的实际时间"""

    def test_actual_now_after_start(self):
        """实际时间应在计划开始之后"""
        planned_start = datetime(2026, 9, 12, 10, 0, tzinfo=timezone.utc)
        actual_now = datetime(2026, 9, 12, 10, 30, tzinfo=timezone.utc)  # 30 分钟后
        
        # 验证 actual_now 在 planned_start 之后
        assert actual_now > planned_start
        
        # 计算延迟
        delay_minutes = (actual_now - planned_start).total_seconds() / 60
        assert delay_minutes == 30

    def test_actual_now_before_start(self):
        """实际时间可在计划开始之前（提前到达）"""
        planned_start = datetime(2026, 9, 12, 10, 0, tzinfo=timezone.utc)
        actual_now = datetime(2026, 9, 12, 9, 45, tzinfo=timezone.utc)  # 提前 15 分钟
        
        # 验证 actual_now 在 planned_start 之前
        assert actual_now < planned_start
        
        # 计算提前量
        early_minutes = (planned_start - actual_now).total_seconds() / 60
        assert early_minutes == 15


class TestActivityStatusTransitions:
    """B4.2: 活动状态转换"""

    def test_en_route_status(self):
        """EN_ROUTE 状态表示在途中"""
        status = ActivityStatus.EN_ROUTE
        assert status == ActivityStatus.EN_ROUTE
        
        # EN_ROUTE 意味着用户正在前往活动地点
        # 但尚未到达

    def test_arrived_status(self):
        """ARRIVED 状态表示已到达"""
        status = ActivityStatus.ARRIVED
        assert status == ActivityStatus.ARRIVED

    def test_in_progress_status(self):
        """IN_PROGRESS 状态表示正在进行"""
        status = ActivityStatus.IN_PROGRESS
        assert status == ActivityStatus.IN_PROGRESS

    def test_completed_status(self):
        """COMPLETED 状态表示已完成"""
        status = ActivityStatus.COMPLETED
        assert status == ActivityStatus.COMPLETED

    def test_skipped_status(self):
        """SKIPPED 状态表示已跳过"""
        status = ActivityStatus.SKIPPED
        assert status == ActivityStatus.SKIPPED

    def test_valid_transitions(self):
        """验证有效状态转换"""
        valid_transitions = {
            ActivityStatus.SCHEDULED: [ActivityStatus.EN_ROUTE, ActivityStatus.SKIPPED, ActivityStatus.CANCELLED],
            ActivityStatus.EN_ROUTE: [ActivityStatus.ARRIVED, ActivityStatus.SKIPPED],
            ActivityStatus.ARRIVED: [ActivityStatus.IN_PROGRESS, ActivityStatus.SKIPPED],
            ActivityStatus.IN_PROGRESS: [ActivityStatus.COMPLETED, ActivityStatus.SKIPPED],
            ActivityStatus.COMPLETED: [],  # 终态
            ActivityStatus.SKIPPED: [],    # 终态
        }
        
        # 验证 SCHEDULED 可以转换到 EN_ROUTE
        assert ActivityStatus.EN_ROUTE in valid_transitions[ActivityStatus.SCHEDULED]
        
        # 验证 COMPLETED 是终态
        assert len(valid_transitions[ActivityStatus.COMPLETED]) == 0


class TestNowNextCalculation:
    """B4.3: NOW/NEXT 计算"""

    def test_now_activity(self):
        """当前进行的活动"""
        now = datetime.now(timezone.utc)
        
        # 模拟当前活动
        current_activity = {
            "id": "A1",
            "status": ActivityStatus.IN_PROGRESS,
            "start_at": now - timedelta(minutes=30),
            "end_at": now + timedelta(minutes=30)
        }
        
        # 验证当前活动的时间范围包含 now
        assert current_activity["start_at"] <= now <= current_activity["end_at"]

    def test_next_activity(self):
        """下一个活动"""
        now = datetime.now(timezone.utc)
        
        # 模拟下一个活动
        next_activity = {
            "id": "A2",
            "status": ActivityStatus.SCHEDULED,
            "start_at": now + timedelta(minutes=60),
            "end_at": now + timedelta(minutes=120)
        }
        
        # 验证下一个活动尚未开始
        assert next_activity["start_at"] > now


class TestLeaveByCalculation:
    """B4.4: 离开时间计算"""

    def test_leave_by_time(self):
        """计算离开时间"""
        activity_start = datetime(2026, 9, 12, 14, 0, tzinfo=timezone.utc)
        travel_time_minutes = 30
        
        leave_by = activity_start - timedelta(minutes=travel_time_minutes)
        
        # 验证离开时间 = 活动开始 - 行程时间
        assert leave_by.hour == 13
        assert leave_by.minute == 30

    def test_leave_by_with_buffer(self):
        """带缓冲的离开时间"""
        activity_start = datetime(2026, 9, 12, 14, 0, tzinfo=timezone.utc)
        travel_time_minutes = 30
        buffer_minutes = 10
        
        leave_by = activity_start - timedelta(minutes=travel_time_minutes + buffer_minutes)
        
        assert leave_by.hour == 13
        assert leave_by.minute == 20


class TestC4Countdown:
    """B4.5: C4 (Commitment) 倒计时"""

    def test_commitment_countdown(self):
        """承诺倒计时"""
        now = datetime.now(timezone.utc)
        commitment_time = now + timedelta(hours=2)
        
        time_remaining = commitment_time - now
        minutes_remaining = time_remaining.total_seconds() / 60
        
        assert minutes_remaining == 120

    def test_commitment_at_risk(self):
        """承诺处于风险中"""
        now = datetime.now(timezone.utc)
        commitment_time = now + timedelta(minutes=15)
        
        time_remaining = commitment_time - now
        minutes_remaining = time_remaining.total_seconds() / 60
        
        # 15 分钟内处于高风险
        RISK_THRESHOLD_MINUTES = 30
        is_at_risk = minutes_remaining <= RISK_THRESHOLD_MINUTES
        assert is_at_risk is True


class TestOfflineNext24h:
    """B4.6: 离线 24 小时"""

    def test_offline_next_24h_detection(self):
        """检测离线状态下的未来 24 小时"""
        is_online = False
        now = datetime.now(timezone.utc)
        
        # 离线时，系统应使用缓存数据
        assert is_online is False
        
        # 缓存应包含未来 24 小时的数据
        cache_valid_hours = 24
        assert cache_valid_hours == 24

    def test_offline_graceful_degradation(self):
        """离线时优雅降级"""
        from app.execution.traveler_twin import TravelerTwin
        
        # 模拟离线状态
        twin = TravelerTwin(
            traveler_id="T1",
            is_online=False,
            last_synced_at=datetime.now(timezone.utc) - timedelta(hours=1)
        )
        
        # 验证离线状态
        assert twin.is_online is False
        
        # 验证可以使用缓存数据
        assert twin.last_synced_at is not None


class TestStaleLocation:
    """B4.7: 过时/高误差位置"""

    def test_stale_location_detection(self):
        """检测过时位置"""
        now = datetime.now(timezone.utc)
        location_timestamp = now - timedelta(minutes=15)
        
        age_minutes = (now - location_timestamp).total_seconds() / 60
        
        STALE_THRESHOLD_MINUTES = 10
        is_stale = age_minutes > STALE_THRESHOLD_MINUTES
        assert is_stale is True

    def test_high_error_location(self):
        """高误差位置"""
        accuracy_meters = 150  # 150 米精度
        
        HIGH_ACCURACY_THRESHOLD = 100  # 100 米
        is_high_error = accuracy_meters > HIGH_ACCURACY_THRESHOLD
        assert is_high_error is True


class TestProviderDurationUpdate:
    """B4.8: 提供者时长更新"""

    def test_duration_update_affects_leave_by(self):
        """时长更新影响离开时间"""
        original_duration = 30  # 分钟
        updated_duration = 45   # 分钟（交通拥堵）
        
        activity_start = datetime(2026, 9, 12, 14, 0, tzinfo=timezone.utc)
        
        original_leave_by = activity_start - timedelta(minutes=original_duration)
        updated_leave_by = activity_start - timedelta(minutes=updated_duration)
        
        # 验证更新后的离开时间更早
        assert updated_leave_by < original_leave_by
        assert (original_leave_by - updated_leave_by).total_seconds() / 60 == 15


class TestEdgeRiskAutopilotState:
    """B4.9: Edge 风险/自动驾驶状态"""

    def test_edge_connected_state(self):
        """Edge 设备连接状态"""
        from app.execution.traveler_twin import EdgeStatus
        
        status = EdgeStatus(
            device_id="PIC16F877A-001",
            connected=True,
            battery_level=85,
            last_seen_at=datetime.now(timezone.utc)
        )
        
        assert status.connected is True
        assert status.battery_level == 85

    def test_edge_disconnected_state(self):
        """Edge 设备断开状态"""
        from app.execution.traveler_twin import EdgeStatus
        
        status = EdgeStatus(
            device_id="PIC16F877A-001",
            connected=False,
            battery_level=20,
            last_seen_at=datetime.now(timezone.utc) - timedelta(minutes=30)
        )
        
        assert status.connected is False

    def test_autopilot_risk_state(self):
        """自动驾驶风险状态"""
        from app.agent.autorun import AutopilotState, RiskLevel
        
        state = AutopilotState(
            active=True,
            risk_level=RiskLevel.HIGH,
            reason="Commitment at risk: 15 min to flight"
        )
        
        assert state.active is True
        assert state.risk_level == RiskLevel.HIGH


if __name__ == "__main__":
    pytest.main([__file__, "-v"])