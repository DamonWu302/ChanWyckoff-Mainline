from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal


MarketRegime = Literal["risk_on", "neutral", "risk_off"]


@dataclass(frozen=True, slots=True)
class MarketIndexEvidence:
    index_code: str
    close: Decimal
    ma20: Decimal
    pct_change: Decimal
    amount: Decimal
    amount_ma20: Decimal


@dataclass(frozen=True, slots=True)
class MarketBreadthEvidence:
    rising_count: int
    falling_count: int
    limit_down_count: int
    strong_theme_count: int


@dataclass(frozen=True, slots=True)
class MarketRegimeResult:
    trade_date: date
    regime: MarketRegime
    score: int
    evidence: dict[str, str | int | Decimal]
    suppress_new_signals: bool


class MarketRegimeService:
    def evaluate(
        self,
        trade_date: date,
        shanghai: MarketIndexEvidence,
        all_a: MarketIndexEvidence,
        breadth: MarketBreadthEvidence,
    ) -> MarketRegimeResult:
        score = 50

        bullish_indices = sum(
            1 for index in (shanghai, all_a) if index.close >= index.ma20 and index.pct_change > 0
        )
        bearish_indices = sum(
            1 for index in (shanghai, all_a) if index.close < index.ma20 and index.pct_change < 0
        )
        if bullish_indices == 2:
            score += 20
            index_trend = "bullish"
        elif bearish_indices == 2:
            score -= 20
            index_trend = "bearish"
        else:
            index_trend = "mixed"

        expanding_amount = sum(1 for index in (shanghai, all_a) if index.amount >= index.amount_ma20)
        if expanding_amount == 2:
            score += 12
            money_flow = "expanding"
        elif expanding_amount == 0:
            score -= 12
            money_flow = "contracting"
        else:
            money_flow = "mixed"

        total_count = max(breadth.rising_count + breadth.falling_count, 1)
        rising_ratio = Decimal(breadth.rising_count) / Decimal(total_count)
        if rising_ratio >= Decimal("0.60"):
            score += 12
            breadth_label = "positive"
        elif rising_ratio <= Decimal("0.40"):
            score -= 12
            breadth_label = "negative"
        else:
            breadth_label = "balanced"

        if breadth.limit_down_count >= 50:
            score -= 10
            limit_down_pressure = "high"
        elif breadth.limit_down_count <= 10:
            score += 5
            limit_down_pressure = "low"
        else:
            limit_down_pressure = "moderate"

        if breadth.strong_theme_count >= 10:
            score += 8
            theme_strength = "broad"
        elif breadth.strong_theme_count <= 3:
            score -= 8
            theme_strength = "thin"
        else:
            theme_strength = "selective"

        score = max(0, min(100, score))
        if score >= 70:
            regime: MarketRegime = "risk_on"
        elif score <= 35:
            regime = "risk_off"
        else:
            regime = "neutral"

        return MarketRegimeResult(
            trade_date=trade_date,
            regime=regime,
            score=score,
            evidence={
                "index_trend": index_trend,
                "money_flow": money_flow,
                "breadth": breadth_label,
                "rising_ratio": rising_ratio,
                "limit_down_pressure": limit_down_pressure,
                "strong_theme_count": breadth.strong_theme_count,
                "theme_strength": theme_strength,
            },
            suppress_new_signals=regime == "risk_off",
        )
