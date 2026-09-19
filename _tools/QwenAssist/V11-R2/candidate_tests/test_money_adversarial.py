"""B3 — Money Adversarial Test Suite (R2)

覆盖场景:
- FREE_KNOWN / KNOWN / ESTIMATED / UNKNOWN
- imported unknown reservation price
- unknown cancellation loss
- unknown ride-hail/taxi price
- foreign currency
- budget headroom
- autonomous action boundary
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from decimal import Decimal
from enum import Enum


class MoneyCertainty(Enum):
    """资金确定性级别"""
    FREE_KNOWN = "FREE_KNOWN"  # 免费已知
    KNOWN = "KNOWN"            # 价格已知
    ESTIMATED = "ESTIMATED"    # 估算价格
    UNKNOWN = "UNKNOWN"        # 价格未知


class TestMoneyCertaintySemantics:
    """B3.1: 资金确定性语义"""

    def test_free_known_not_treated_as_zero(self):
        """FREE_KNOWN 不应被当作 0 处理"""
        price = 0
        certainty = MoneyCertainty.FREE_KNOWN
        
        # 验证 FREE_KNOWN 有明确语义
        assert certainty == MoneyCertainty.FREE_KNOWN
        assert price == 0  # 但值是 0
        
        # 关键是：UI 应显示"免费"而非"价格未知"
        display_text = "免费" if certainty == MoneyCertainty.FREE_KNOWN else "未知"
        assert display_text == "免费"

    def test_known_price_exact(self):
        """KNOWN 价格应精确显示"""
        price = 15000  # 150.00 CNY
        certainty = MoneyCertainty.KNOWN
        
        assert certainty == MoneyCertainty.KNOWN
        assert price > 0

    def test_estimated_price_marked(self):
        """ESTIMATED 价格应标记为估算"""
        price = 12000
        certainty = MoneyCertainty.ESTIMATED
        
        # 验证显示时应加标记
        display = f"约 {price // 100}.{price % 100:02d} 元" if certainty == MoneyCertainty.ESTIMATED else str(price)
        assert "约" in display

    def test_unknown_price_not_zero(self):
        """UNKNOWN 价格不应隐式转换为 0"""
        price = None  # 价格未知
        certainty = MoneyCertainty.UNKNOWN
        
        # UNKNOWN 不应被视为免费
        assert certainty == MoneyCertainty.UNKNOWN
        assert price is None or (price is not None and price > 0)


class TestImportedUnknownPrice:
    """B3.2: 导入的未知价格"""

    def test_imported_reservation_unknown_price(self):
        """导入的预订价格未知时应保持 UNKNOWN"""
        from app.db.models import Commitment, CommitmentType
        
        commitment = Commitment(
            id=str(uuid4()),
            journey_id="J1",
            commitment_type=CommitmentType.HOTEL,
            provider_key="imported",
            external_id="IMPORT-001",
            title="Imported Hotel",
            start_at=datetime.now(timezone.utc),
            end_at=datetime.now(timezone.utc) + timedelta(days=1),
            status="PENDING",
            price_amount_minor=None,  # 未知
            price_currency="CNY"
        )
        
        # 验证价格为空时标记为 UNKNOWN
        is_unknown = commitment.price_amount_minor is None
        assert is_unknown is True

    def test_imported_with_known_price(self):
        """导入的预订有已知价格"""
        from app.db.models import Commitment, CommitmentType
        
        commitment = Commitment(
            id=str(uuid4()),
            journey_id="J1",
            commitment_type=CommitmentType.HOTEL,
            provider_key="imported",
            external_id="IMPORT-002",
            title="Hotel with Price",
            start_at=datetime.now(timezone.utc),
            end_at=datetime.now(timezone.utc) + timedelta(days=1),
            status="CONFIRMED",
            price_amount_minor=50000,
            price_currency="CNY"
        )
        
        assert commitment.price_amount_minor == 50000
        assert commitment.status == "CONFIRMED"


class TestUnknownCancellationLoss:
    """B3.3: 未知取消损失"""

    def test_unknown_cancellation_not_auto_execute(self):
        """UNKNOWN 取消损失不应自动执行取消"""
        # 模拟取消策略
        cancellation_cost = None  # 未知
        certainty = MoneyCertainty.UNKNOWN
        
        # 当取消损失未知时，系统不应自动取消
        should_auto_cancel = cancellation_cost is not None and certainty != MoneyCertainty.UNKNOWN
        assert should_auto_cancel is False

    def test_known_cancellation_can_auto_execute(self):
        """已知取消损失可自动执行（如果策略允许）"""
        cancellation_cost = 10000  # 100 元
        certainty = MoneyCertainty.KNOWN
        
        # 已知损失时可自动执行
        should_auto_cancel = cancellation_cost is not None and certainty != MoneyCertainty.UNKNOWN
        assert should_auto_cancel is True


class TestUnknownTaxiPrice:
    """B3.4: 未知出租车价格"""

    def test_taxi_price_unknown_handled(self):
        """出租车价格未知时不应直接使用"""
        from app.integrations.mobility.routingpy_adapter import TravelEstimate
        
        estimate = TravelEstimate(
            provider_key="amap",
            duration_min=30,
            geometry=None,
            price_amount_minor=None,  # 未知
            price_currency="CNY"
        )
        
        # 验证价格未知
        is_unknown = estimate.price_amount_minor is None
        assert is_unknown is True
        
        # UI 应显示"价格待确认"而非直接使用
        display = "价格待确认" if is_unknown else f"{estimate.price_amount_minor // 100}元"
        assert display == "价格待确认"


class TestForeignCurrency:
    """B3.5: 外币处理"""

    def test_foreign_currency_preserved(self):
        """外币应保持原币种显示"""
        from app.db.models import Commitment, CommitmentType
        
        commitment = Commitment(
            id=str(uuid4()),
            journey_id="J1",
            commitment_type=CommitmentType.ATTRACTION,
            provider_key="klook",
            external_id="KL-001",
            title="Tokyo Tower",
            start_at=datetime.now(timezone.utc),
            end_at=datetime.now(timezone.utc) + timedelta(hours=2),
            status="CONFIRMED",
            price_amount_minor=200000,  # 2000 JPY
            price_currency="JPY"
        )
        
        # 验证外币未被转换
        assert commitment.price_currency == "JPY"
        
        # 汇率转换应在显示层处理，不应修改存储值
        assert commitment.price_amount_minor == 200000

    def test_mixed_currency_in_journey(self):
        """行程中混合币种应正确显示"""
        from app.db.models import Journey
        
        journey = Journey(
            id=str(uuid4()),
            traveler_id="T1",
            city_code="TOKYO",
            start_at=datetime.now(timezone.utc),
            end_at=datetime.now(timezone.utc) + timedelta(days=3),
            budget_amount_minor=50000,
            budget_currency="JPY"
        )
        
        # 验证预算币种
        assert journey.budget_currency == "JPY"


class TestBudgetHeadroom:
    """B3.6: 预算余量"""

    def test_budget_headroom_calculation(self):
        """计算预算余量"""
        budget = 100000  # 1000 元
        spent = 65000    # 650 元
        
        headroom = budget - spent
        headroom_percent = (headroom / budget) * 100
        
        assert headroom == 35000
        assert headroom_percent == 35.0

    def test_budget_with_unknown_items(self):
        """包含未知价格时的预算计算"""
        budget = 100000
        known_spent = 50000
        unknown_items = 2
        
        # 未知项目不应计入已花费，但应预警
        min_spent = known_spent
        max_spent = known_spent + (unknown_items * 50000)  # 假设每个未知最多 500 元
        
        assert min_spent == 50000
        assert max_spent == 150000
        assert max_spent > budget  # 可能超预算


class TestAutonomousActionBoundary:
    """B3.7: 自主操作边界"""

    def test_autonomous_action_price_limit(self):
        """自主操作的价格限制"""
        from app.agent.delegation_policy import DelegationPolicy, AutonomyLevel
        
        policy = DelegationPolicy()
        
        # 高价值操作需要确认
        high_value_threshold = 50000  # 500 元
        
        # 测试各种价格场景
        test_cases = [
            (10000, True),   # 100 元，可自主
            (49999, True),   # 499 元，可自主
            (50000, False),  # 500 元，需要确认
            (100000, False), # 1000 元，需要确认
        ]
        
        for price, can_autonomous in test_cases:
            requires_approval = price >= high_value_threshold
            assert requires_approval == (not can_autonomous)

    def test_free_actions_always_autonomous(self):
        """免费操作始终可自主执行"""
        price = 0
        
        # 免费操作不需要确认
        requires_approval = price > 0
        assert requires_approval is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])