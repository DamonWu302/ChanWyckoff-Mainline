from datetime import date
from decimal import Decimal

from app.selection.market_regime import (
    MarketBreadthEvidence,
    MarketIndexEvidence,
    MarketRegimeService,
)


def test_market_regime_is_risk_on_when_indices_and_breadth_confirm() -> None:
    service = MarketRegimeService()

    result = service.evaluate(
        trade_date=date(2026, 5, 25),
        shanghai=MarketIndexEvidence(
            index_code="000001.SH",
            close=Decimal("3148"),
            ma20=Decimal("3090"),
            pct_change=Decimal("1.2"),
            amount=Decimal("410000000000"),
            amount_ma20=Decimal("330000000000"),
        ),
        all_a=MarketIndexEvidence(
            index_code="000985.CSI",
            close=Decimal("4980"),
            ma20=Decimal("4850"),
            pct_change=Decimal("1.5"),
            amount=Decimal("980000000000"),
            amount_ma20=Decimal("760000000000"),
        ),
        breadth=MarketBreadthEvidence(
            rising_count=3800,
            falling_count=1200,
            limit_down_count=5,
            strong_theme_count=18,
        ),
    )

    assert result.regime == "risk_on"
    assert result.score >= 70
    assert result.evidence["index_trend"] == "bullish"
    assert result.evidence["money_flow"] == "expanding"
    assert result.evidence["breadth"] == "positive"
    assert result.suppress_new_signals is False


def test_market_regime_is_risk_off_when_indices_break_and_breadth_is_weak() -> None:
    service = MarketRegimeService()

    result = service.evaluate(
        trade_date=date(2026, 5, 25),
        shanghai=MarketIndexEvidence(
            index_code="000001.SH",
            close=Decimal("2960"),
            ma20=Decimal("3090"),
            pct_change=Decimal("-1.8"),
            amount=Decimal("300000000000"),
            amount_ma20=Decimal("360000000000"),
        ),
        all_a=MarketIndexEvidence(
            index_code="000985.CSI",
            close=Decimal("4650"),
            ma20=Decimal("4850"),
            pct_change=Decimal("-2.4"),
            amount=Decimal("700000000000"),
            amount_ma20=Decimal("860000000000"),
        ),
        breadth=MarketBreadthEvidence(
            rising_count=900,
            falling_count=4100,
            limit_down_count=95,
            strong_theme_count=2,
        ),
    )

    assert result.regime == "risk_off"
    assert result.score <= 35
    assert result.evidence["index_trend"] == "bearish"
    assert result.evidence["money_flow"] == "contracting"
    assert result.evidence["breadth"] == "negative"
    assert result.suppress_new_signals is True
