from datetime import date
from decimal import Decimal

from app.selection.theme_strength import (
    CoreStockEvidence,
    ThemeStrengthEvidence,
    ThemeStrengthService,
)


def test_theme_strength_labels_confirmed_mainline_with_core_stock_ranking() -> None:
    service = ThemeStrengthService()

    result = service.evaluate(
        trade_date=date(2026, 5, 25),
        themes=[
            ThemeStrengthEvidence(
                theme_code="AI",
                theme_name="人工智能",
                rs_3=Decimal("0.08"),
                rs_5=Decimal("0.11"),
                rs_10=Decimal("0.16"),
                rs_20=Decimal("0.24"),
                amount_ratio_20=Decimal("1.85"),
                rising_count=42,
                limit_up_count=6,
                new_high_count=9,
                resisted_in_weak_market=True,
            ),
            ThemeStrengthEvidence(
                theme_code="WINE",
                theme_name="白酒",
                rs_3=Decimal("0.01"),
                rs_5=Decimal("0.02"),
                rs_10=Decimal("0.03"),
                rs_20=Decimal("0.05"),
                amount_ratio_20=Decimal("0.95"),
                rising_count=18,
                limit_up_count=0,
                new_high_count=1,
                resisted_in_weak_market=False,
            ),
        ],
        core_stocks={
            "AI": [
                CoreStockEvidence(
                    ts_code="600001.SH",
                    name="AI核心A",
                    multi_period_rs=Decimal("0.28"),
                    amount_expansion=Decimal("2.1"),
                    theme_profit_effect=Decimal("0.82"),
                    market_cap=Decimal("62000000000"),
                    turnover_rate=Decimal("4.5"),
                ),
                CoreStockEvidence(
                    ts_code="600002.SH",
                    name="AI后排B",
                    multi_period_rs=Decimal("0.34"),
                    amount_expansion=Decimal("1.1"),
                    theme_profit_effect=Decimal("0.50"),
                    market_cap=Decimal("9000000000"),
                    turnover_rate=Decimal("2.2"),
                ),
            ]
        },
    )

    ai_theme = result.themes[0]

    assert ai_theme.theme_code == "AI"
    assert ai_theme.label == "confirmed_mainline"
    assert ai_theme.score > result.themes[1].score
    assert ai_theme.core_stocks[0].ts_code == "600001.SH"
    assert ai_theme.core_stocks[0].rank == 1
    assert ai_theme.core_stocks[0].score > ai_theme.core_stocks[1].score
    assert result.themes[1].label == "watch"
