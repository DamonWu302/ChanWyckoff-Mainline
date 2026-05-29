from datetime import date, datetime, timezone
from decimal import Decimal

from app.dashboard.snapshot import DashboardSignalInput, OperationsDashboardBuilder
from app.selection.market_regime import MarketRegimeResult
from app.selection.theme_strength import (
    CoreStockEvidence,
    RankedCoreStock,
    RankedTheme,
    ThemeStrengthEvidence,
    ThemeStrengthResult,
)


def test_build_operations_snapshot_uses_requested_trade_date() -> None:
    from app.dashboard.snapshot import build_operations_snapshot

    snapshot = build_operations_snapshot(trade_date=date(2026, 5, 29))

    assert snapshot["trade_date"] == "2026-05-29"


def test_dashboard_builder_aggregates_regime_mainlines_core_stocks_and_signals() -> None:
    trade_date = date(2026, 5, 26)
    regime = MarketRegimeResult(
        trade_date=trade_date,
        regime="risk_off",
        score=30,
        evidence={"breadth": "negative", "theme_strength": "thin"},
        suppress_new_signals=True,
    )
    theme = RankedTheme(
        theme_code="BK1234",
        theme_name="机器人",
        score=88,
        label="confirmed_mainline",
        evidence=ThemeStrengthEvidence(
            theme_code="BK1234",
            theme_name="机器人",
            rs_3=Decimal("0.12"),
            rs_5=Decimal("0.15"),
            rs_10=Decimal("0.18"),
            rs_20=Decimal("0.20"),
            amount_ratio_20=Decimal("1.62"),
            rising_count=18,
            limit_up_count=4,
            new_high_count=6,
            resisted_in_weak_market=True,
        ),
        core_stocks=[
            RankedCoreStock(
                rank=1,
                ts_code="600001.SH",
                name="机器人核心 Alpha",
                score=91,
                evidence=CoreStockEvidence(
                    ts_code="600001.SH",
                    name="机器人核心 Alpha",
                    multi_period_rs=Decimal("0.28"),
                    amount_expansion=Decimal("2.1"),
                    theme_profit_effect=Decimal("0.72"),
                    market_cap=Decimal("65000000000"),
                    turnover_rate=Decimal("4.8"),
                ),
            )
        ],
    )
    signals = [
        DashboardSignalInput(
            ts_code="600001.SH",
            name="机器人核心 Alpha",
            theme="机器人",
            state="confirmed_3buy",
            score=86,
            suggested_action="upgrade_position",
            amount=Decimal("200000000"),
            signal_time=datetime(2026, 5, 26, 14, 0, tzinfo=timezone.utc),
            structure_evidence="30m_platform_upper_breakout",
            volume_price_evidence="breakout_expansion_pullback_shrinking",
            wyckoff_forecast="continuation_expected",
        )
    ]

    snapshot = OperationsDashboardBuilder().build(
        market_regime=regime,
        theme_strength=ThemeStrengthResult(trade_date=trade_date, themes=[theme]),
        signals=signals,
    )

    assert snapshot["trade_date"] == "2026-05-26"
    assert snapshot["market_regime"]["state"] == "risk_off"
    assert snapshot["market_regime"]["attack_allowed"] is False
    assert snapshot["market_regime"]["suppress_new_signals"] is True
    assert snapshot["market_regime"]["recommended_exposure_pct"] == 10
    assert snapshot["mainlines"][0]["theme"] == "机器人"
    assert snapshot["mainlines"][0]["core_stocks"][0]["ts_code"] == "600001.SH"
    assert snapshot["signals"][0]["signal_time"] == "2026-05-26T14:00:00+00:00"
    assert snapshot["filters"]["themes"] == ["机器人"]
