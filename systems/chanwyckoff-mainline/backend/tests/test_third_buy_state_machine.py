from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.signals.third_buy import (
    BreakoutBar,
    PullbackBar,
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


def test_shrinking_pullback_near_upper_upgrades_to_confirmed_3buy() -> None:
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
    pullbacks = [
        PullbackBar(
            bar_time=breakout.bar_time + timedelta(minutes=30),
            open=Decimal("10.88"),
            high=Decimal("10.92"),
            low=Decimal("10.55"),
            close=Decimal("10.70"),
            volume=820000,
            amount=Decimal("90000000"),
            atr=Decimal("0.34"),
        ),
        PullbackBar(
            bar_time=breakout.bar_time + timedelta(minutes=60),
            open=Decimal("10.72"),
            high=Decimal("10.86"),
            low=Decimal("10.48"),
            close=Decimal("10.68"),
            volume=760000,
            amount=Decimal("84000000"),
            atr=Decimal("0.34"),
        ),
    ]
    service = ThirdBuySignalService()
    proto_signal = service.evaluate_breakout(structure, breakout)

    confirmed_signal = service.evaluate_pullback(structure, breakout, pullbacks)

    assert proto_signal is not None
    assert confirmed_signal is not None
    assert confirmed_signal.state == "confirmed_3buy"
    assert confirmed_signal.action == "upgrade_position"
    assert confirmed_signal.wyckoff.features["pullback_volume"] == "shrinking"
    assert confirmed_signal.wyckoff.features["support_quality"] == "accepted_above_upper"
    assert confirmed_signal.wyckoff.forecast == "continuation_expected"


def test_heavy_volume_close_back_into_structure_outputs_failed_3buy() -> None:
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
    pullbacks = [
        PullbackBar(
            bar_time=breakout.bar_time + timedelta(minutes=30),
            open=Decimal("10.70"),
            high=Decimal("10.76"),
            low=Decimal("10.05"),
            close=Decimal("10.18"),
            volume=1600000,
            amount=Decimal("168000000"),
            atr=Decimal("0.34"),
        )
    ]
    service = ThirdBuySignalService()

    failed_signal = service.evaluate_pullback(structure, breakout, pullbacks)

    assert failed_signal is not None
    assert failed_signal.state == "failed_3buy"
    assert failed_signal.action == "filter"
    assert failed_signal.wyckoff.features["failure_reason"] == "heavy_volume_close_back_inside"
    assert failed_signal.wyckoff.forecast == "supply_returned"


def test_timeout_without_valid_pullback_confirmation_outputs_failed_3buy() -> None:
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
    pullbacks = [
        PullbackBar(
            bar_time=breakout.bar_time + timedelta(minutes=30 * index),
            open=Decimal("11.10"),
            high=Decimal("11.30"),
            low=Decimal("10.95"),
            close=Decimal("11.05"),
            volume=900000,
            amount=Decimal("99000000"),
            atr=Decimal("0.34"),
        )
        for index in range(1, 10)
    ]
    service = ThirdBuySignalService()

    failed_signal = service.evaluate_pullback(structure, breakout, pullbacks)

    assert failed_signal is not None
    assert failed_signal.state == "failed_3buy"
    assert failed_signal.action == "filter"
    assert failed_signal.wyckoff.features["failure_reason"] == "pullback_timeout"
    assert failed_signal.wyckoff.forecast == "confirmation_expired"
