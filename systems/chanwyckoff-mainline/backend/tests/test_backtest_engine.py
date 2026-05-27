from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.backtest.engine import (
    BacktestBar,
    BacktestConfig,
    BacktestEngine,
    BacktestParameterSet,
    SignalCandidate,
)


def test_confirmed_signal_enters_next_30m_bar_and_exits_on_target_with_costs() -> None:
    signal_time = datetime(2026, 5, 25, 10, 0, tzinfo=timezone.utc)
    signal = SignalCandidate(
        ts_code="600001.SH",
        state="confirmed_3buy",
        signal_time=signal_time,
        wyckoff_score=86,
        structure_upper=Decimal("10.60"),
        structure_lower=Decimal("9.80"),
        target_price=Decimal("11.40"),
    )
    bars = [
        BacktestBar(
            ts_code="600001.SH",
            bar_time=signal_time,
            open=Decimal("10.70"),
            high=Decimal("10.90"),
            low=Decimal("10.55"),
            close=Decimal("10.80"),
            volume=1_000_000,
            amount=Decimal("108000000"),
        ),
        BacktestBar(
            ts_code="600001.SH",
            bar_time=signal_time + timedelta(minutes=30),
            open=Decimal("10.90"),
            high=Decimal("11.20"),
            low=Decimal("10.84"),
            close=Decimal("11.05"),
            volume=1_100_000,
            amount=Decimal("121000000"),
        ),
        BacktestBar(
            ts_code="600001.SH",
            bar_time=signal_time + timedelta(minutes=60),
            open=Decimal("11.05"),
            high=Decimal("11.55"),
            low=Decimal("10.95"),
            close=Decimal("11.45"),
            volume=1_300_000,
            amount=Decimal("148850000"),
        ),
    ]
    engine = BacktestEngine(
        BacktestConfig(
            initial_cash=Decimal("100000"),
            position_pct=Decimal("0.50"),
            commission_rate=Decimal("0.0003"),
            stamp_tax_rate=Decimal("0.001"),
            slippage_rate=Decimal("0.001"),
            max_holding_bars=8,
        )
    )

    report = engine.run(signals=[signal], bars=bars)

    assert len(report.trades) == 1
    trade = report.trades[0]
    assert trade.ts_code == "600001.SH"
    assert trade.signal_state == "confirmed_3buy"
    assert trade.entry_time == signal_time + timedelta(minutes=30)
    assert trade.exit_time == signal_time + timedelta(minutes=60)
    assert trade.entry_price == Decimal("10.9109")
    assert trade.exit_price == Decimal("11.3886")
    assert trade.exit_reason == "target_reached"
    assert trade.holding_bars == 1
    assert trade.net_return == Decimal("0.042112")
    assert report.total_trades == 1
    assert report.win_rate == Decimal("1")
    assert report.mean_return == trade.net_return
    assert report.max_drawdown == Decimal("0")
    assert report.by_signal_state["confirmed_3buy"].win_rate == Decimal("1")
    assert report.by_wyckoff_bucket["80-100"].mean_return == trade.net_return


def test_limit_up_delays_entry_and_limit_down_delays_stop_exit() -> None:
    signal_time = datetime(2026, 5, 25, 10, 0, tzinfo=timezone.utc)
    signal = SignalCandidate(
        ts_code="600002.SH",
        state="proto_3buy",
        signal_time=signal_time,
        wyckoff_score=63,
        structure_upper=Decimal("10.60"),
        structure_lower=Decimal("9.80"),
        target_price=Decimal("11.40"),
    )
    bars = [
        BacktestBar(
            ts_code="600002.SH",
            bar_time=signal_time + timedelta(minutes=30),
            open=Decimal("10.90"),
            high=Decimal("10.90"),
            low=Decimal("10.90"),
            close=Decimal("10.90"),
            volume=500_000,
            amount=Decimal("54500000"),
            limit_up=True,
        ),
        BacktestBar(
            ts_code="600002.SH",
            bar_time=signal_time + timedelta(minutes=60),
            open=Decimal("10.70"),
            high=Decimal("10.78"),
            low=Decimal("10.40"),
            close=Decimal("10.45"),
            volume=900_000,
            amount=Decimal("94050000"),
        ),
        BacktestBar(
            ts_code="600002.SH",
            bar_time=signal_time + timedelta(minutes=90),
            open=Decimal("9.70"),
            high=Decimal("9.70"),
            low=Decimal("9.70"),
            close=Decimal("9.70"),
            volume=1_600_000,
            amount=Decimal("155200000"),
            limit_down=True,
        ),
        BacktestBar(
            ts_code="600002.SH",
            bar_time=signal_time + timedelta(minutes=120),
            open=Decimal("9.74"),
            high=Decimal("9.92"),
            low=Decimal("9.72"),
            close=Decimal("9.84"),
            volume=1_300_000,
            amount=Decimal("127920000"),
        ),
    ]
    engine = BacktestEngine(
        BacktestConfig(
            initial_cash=Decimal("100000"),
            position_pct=Decimal("0.50"),
            commission_rate=Decimal("0.0003"),
            stamp_tax_rate=Decimal("0.001"),
            slippage_rate=Decimal("0.001"),
            max_holding_bars=8,
        )
    )

    report = engine.run(signals=[signal], bars=bars)

    assert len(report.trades) == 1
    trade = report.trades[0]
    assert trade.entry_time == signal_time + timedelta(minutes=60)
    assert trade.exit_time == signal_time + timedelta(minutes=120)
    assert trade.entry_price == Decimal("10.7107")
    assert trade.exit_price == Decimal("9.7902")
    assert trade.exit_reason == "stop_loss"
    assert trade.holding_bars == 2
    assert report.max_drawdown == Decimal("0.043702")
    assert report.by_signal_state["proto_3buy"].win_rate == Decimal("0")
    assert report.by_wyckoff_bucket["60-79"].total_trades == 1


def test_grid_search_filters_date_range_and_flags_small_concentrated_samples() -> None:
    base_time = datetime(2026, 5, 25, 10, 0, tzinfo=timezone.utc)
    signals = [
        SignalCandidate(
            ts_code="600001.SH",
            state="confirmed_3buy",
            signal_time=base_time - timedelta(days=3),
            wyckoff_score=82,
            structure_upper=Decimal("10.60"),
            structure_lower=Decimal("9.80"),
            target_price=Decimal("11.40"),
        ),
        SignalCandidate(
            ts_code="600001.SH",
            state="confirmed_3buy",
            signal_time=base_time,
            wyckoff_score=82,
            structure_upper=Decimal("10.60"),
            structure_lower=Decimal("9.80"),
            target_price=Decimal("11.40"),
        ),
        SignalCandidate(
            ts_code="600001.SH",
            state="proto_3buy",
            signal_time=base_time + timedelta(days=1),
            wyckoff_score=66,
            structure_upper=Decimal("10.60"),
            structure_lower=Decimal("9.80"),
            target_price=Decimal("11.40"),
        ),
    ]
    bars = [
        BacktestBar(
            ts_code="600001.SH",
            bar_time=base_time + timedelta(minutes=30),
            open=Decimal("10.90"),
            high=Decimal("10.95"),
            low=Decimal("10.80"),
            close=Decimal("10.88"),
            volume=1_000_000,
            amount=Decimal("108800000"),
        ),
        BacktestBar(
            ts_code="600001.SH",
            bar_time=base_time + timedelta(minutes=60),
            open=Decimal("10.88"),
            high=Decimal("11.50"),
            low=Decimal("10.82"),
            close=Decimal("11.42"),
            volume=1_200_000,
            amount=Decimal("137040000"),
        ),
        BacktestBar(
            ts_code="600001.SH",
            bar_time=base_time + timedelta(days=1, minutes=30),
            open=Decimal("10.70"),
            high=Decimal("10.82"),
            low=Decimal("10.30"),
            close=Decimal("10.36"),
            volume=900_000,
            amount=Decimal("93240000"),
        ),
        BacktestBar(
            ts_code="600001.SH",
            bar_time=base_time + timedelta(days=1, minutes=60),
            open=Decimal("10.34"),
            high=Decimal("10.40"),
            low=Decimal("9.76"),
            close=Decimal("9.82"),
            volume=1_400_000,
            amount=Decimal("137480000"),
        ),
    ]
    engine = BacktestEngine(
        BacktestConfig(
            initial_cash=Decimal("100000"),
            position_pct=Decimal("0.50"),
            commission_rate=Decimal("0.0003"),
            stamp_tax_rate=Decimal("0.001"),
            slippage_rate=Decimal("0.001"),
            max_holding_bars=8,
        )
    )

    grid_report = engine.run_grid_search(
        signals=signals,
        bars=bars,
        start=base_time,
        end=base_time + timedelta(days=2),
        parameter_sets=[
            BacktestParameterSet(name="fast", max_holding_bars=1),
            BacktestParameterSet(name="patient", max_holding_bars=8),
        ],
        min_trades_for_robust=5,
        max_symbol_concentration=Decimal("0.60"),
    )

    assert [result.name for result in grid_report.results] == ["fast", "patient"]
    assert grid_report.results[0].report.total_trades == 2
    assert grid_report.results[0].risk_flags == ["small_sample", "symbol_concentration"]
    assert grid_report.results[0].symbol_concentration["600001.SH"] == Decimal("1")
    assert grid_report.best.name == "fast"
    assert grid_report.reliability_note == "theme_history_reliability_requires_point_in_time_constituents"


def test_overlapping_positions_respect_total_theme_and_symbol_capacity_limits() -> None:
    signal_time = datetime(2026, 5, 25, 10, 0, tzinfo=timezone.utc)
    signals = [
        SignalCandidate(
            ts_code="600001.SH",
            state="confirmed_3buy",
            signal_time=signal_time,
            wyckoff_score=86,
            structure_upper=Decimal("10.60"),
            structure_lower=Decimal("9.80"),
            target_price=Decimal("11.40"),
            theme="机器人",
        ),
        SignalCandidate(
            ts_code="600002.SH",
            state="confirmed_3buy",
            signal_time=signal_time + timedelta(minutes=1),
            wyckoff_score=84,
            structure_upper=Decimal("20.60"),
            structure_lower=Decimal("19.80"),
            target_price=Decimal("21.40"),
            theme="机器人",
        ),
    ]
    bars = [
        BacktestBar(
            ts_code="600001.SH",
            bar_time=signal_time + timedelta(minutes=30),
            open=Decimal("10.90"),
            high=Decimal("11.05"),
            low=Decimal("10.84"),
            close=Decimal("11.00"),
            volume=1_000_000,
            amount=Decimal("110000000"),
        ),
        BacktestBar(
            ts_code="600001.SH",
            bar_time=signal_time + timedelta(minutes=60),
            open=Decimal("11.00"),
            high=Decimal("11.50"),
            low=Decimal("10.92"),
            close=Decimal("11.42"),
            volume=1_100_000,
            amount=Decimal("125620000"),
        ),
        BacktestBar(
            ts_code="600002.SH",
            bar_time=signal_time + timedelta(minutes=30),
            open=Decimal("20.90"),
            high=Decimal("21.05"),
            low=Decimal("20.84"),
            close=Decimal("21.00"),
            volume=1_000_000,
            amount=Decimal("210000000"),
        ),
        BacktestBar(
            ts_code="600002.SH",
            bar_time=signal_time + timedelta(minutes=60),
            open=Decimal("21.00"),
            high=Decimal("21.50"),
            low=Decimal("20.92"),
            close=Decimal("21.42"),
            volume=1_100_000,
            amount=Decimal("235620000"),
        ),
    ]
    engine = BacktestEngine(
        BacktestConfig(
            initial_cash=Decimal("100000"),
            position_pct=Decimal("0.40"),
            commission_rate=Decimal("0.0003"),
            stamp_tax_rate=Decimal("0.001"),
            slippage_rate=Decimal("0.001"),
            max_holding_bars=8,
            max_total_position_pct=Decimal("0.70"),
            max_theme_position_pct=Decimal("0.50"),
            max_symbol_position_pct=Decimal("0.40"),
        )
    )

    report = engine.run(signals=signals, bars=bars)

    assert [trade.ts_code for trade in report.trades] == ["600001.SH"]
    assert len(report.skipped_signals) == 1
    assert report.skipped_signals[0].ts_code == "600002.SH"
    assert report.skipped_signals[0].reason == "theme_capacity_exceeded"
