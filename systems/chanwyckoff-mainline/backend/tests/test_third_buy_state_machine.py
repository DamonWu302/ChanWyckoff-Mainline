from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.signals.third_buy import (
    BreakoutBar,
    ThirdBuySignalService,
    ThirdBuyStructure,
)


def test_strong_breakout_above_structure_outputs_proto_3buy() -> None:
    structure = ThirdBuyStructure(
        ts_code="600001.SH",
        upper=Decimal("10.60"),
        lower=Decimal("9.80"),
        mid=Decimal("10.20"),
        quality_score=82,
        platform_avg_volume=1000000,
    )
    breakout = BreakoutBar(
        bar_time=datetime(2026, 5, 25, 14, 30, tzinfo=timezone.utc),
        open=Decimal("10.55"),
        high=Decimal("11.10"),
        low=Decimal("10.50"),
        close=Decimal("10.95"),
        volume=1850000,
        amount=Decimal("200000000"),
    )
    service = ThirdBuySignalService()

    signal = service.evaluate_breakout(structure, breakout)

    assert signal is not None
    assert signal.state == "proto_3buy"
    assert signal.action == "light_position"
    assert signal.structure_score == 82
    assert signal.wyckoff.background == "constructive"
    assert signal.wyckoff.features["volume_expansion"] == "confirmed"
    assert signal.wyckoff.forecast == "wait_pullback_confirmation"
    assert signal.wyckoff.score >= 70


def test_breakout_without_close_confirmation_is_ignored() -> None:
    structure = ThirdBuyStructure(
        ts_code="600001.SH",
        upper=Decimal("10.60"),
        lower=Decimal("9.80"),
        mid=Decimal("10.20"),
        quality_score=82,
        platform_avg_volume=1000000,
    )
    breakout = BreakoutBar(
        bar_time=datetime(2026, 5, 25, 14, 30, tzinfo=timezone.utc) + timedelta(minutes=30),
        open=Decimal("10.55"),
        high=Decimal("10.90"),
        low=Decimal("10.20"),
        close=Decimal("10.58"),
        volume=1800000,
        amount=Decimal("180000000"),
    )
    service = ThirdBuySignalService()

    signal = service.evaluate_breakout(structure, breakout)

    assert signal is None
