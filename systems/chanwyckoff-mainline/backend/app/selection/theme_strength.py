from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Literal


ThemeLabel = Literal[
    "resistant_theme",
    "emerging_leader",
    "confirmed_mainline",
    "exhausted_theme",
    "watch",
]


@dataclass(frozen=True, slots=True)
class ThemeStrengthEvidence:
    theme_code: str
    theme_name: str
    rs_3: Decimal
    rs_5: Decimal
    rs_10: Decimal
    rs_20: Decimal
    amount_ratio_20: Decimal
    rising_count: int
    limit_up_count: int
    new_high_count: int
    resisted_in_weak_market: bool


@dataclass(frozen=True, slots=True)
class CoreStockEvidence:
    ts_code: str
    name: str
    multi_period_rs: Decimal
    amount_expansion: Decimal
    theme_profit_effect: Decimal
    market_cap: Decimal
    turnover_rate: Decimal


@dataclass(frozen=True, slots=True)
class RankedCoreStock:
    rank: int
    ts_code: str
    name: str
    score: int
    evidence: CoreStockEvidence


@dataclass(frozen=True, slots=True)
class RankedTheme:
    theme_code: str
    theme_name: str
    score: int
    label: ThemeLabel
    evidence: ThemeStrengthEvidence
    core_stocks: list[RankedCoreStock] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class ThemeStrengthResult:
    trade_date: date
    themes: list[RankedTheme]


class ThemeStrengthService:
    def evaluate(
        self,
        trade_date: date,
        themes: list[ThemeStrengthEvidence],
        core_stocks: dict[str, list[CoreStockEvidence]] | None = None,
    ) -> ThemeStrengthResult:
        core_stocks = core_stocks or {}
        ranked_themes = [
            RankedTheme(
                theme_code=theme.theme_code,
                theme_name=theme.theme_name,
                score=self._theme_score(theme),
                label=self._theme_label(theme),
                evidence=theme,
                core_stocks=self._rank_core_stocks(core_stocks.get(theme.theme_code, [])),
            )
            for theme in themes
        ]
        ranked_themes.sort(key=lambda item: item.score, reverse=True)
        return ThemeStrengthResult(trade_date=trade_date, themes=ranked_themes)

    def _theme_score(self, theme: ThemeStrengthEvidence) -> int:
        rs_score = self._clamp_decimal(
            (theme.rs_3 * Decimal("0.20"))
            + (theme.rs_5 * Decimal("0.25"))
            + (theme.rs_10 * Decimal("0.25"))
            + (theme.rs_20 * Decimal("0.30")),
            Decimal("-0.10"),
            Decimal("0.30"),
        )
        amount_score = self._clamp_decimal(
            theme.amount_ratio_20 - Decimal("1.0"),
            Decimal("-0.30"),
            Decimal("1.20"),
        )
        profit_score = Decimal(theme.rising_count) * Decimal("0.35")
        limit_score = Decimal(theme.limit_up_count) * Decimal("2.0")
        high_score = Decimal(theme.new_high_count) * Decimal("1.5")
        resistant_bonus = Decimal("8") if theme.resisted_in_weak_market else Decimal("0")

        score = (
            Decimal("35")
            + rs_score * Decimal("140")
            + amount_score * Decimal("18")
            + profit_score
            + limit_score
            + high_score
            + resistant_bonus
        )
        return max(0, min(100, int(score)))

    def _theme_label(self, theme: ThemeStrengthEvidence) -> ThemeLabel:
        score = self._theme_score(theme)
        if score >= 78 and theme.amount_ratio_20 >= Decimal("1.5"):
            return "confirmed_mainline"
        if theme.resisted_in_weak_market and score >= 65:
            return "resistant_theme"
        if score >= 65:
            return "emerging_leader"
        if theme.amount_ratio_20 < Decimal("0.8") and theme.rs_5 < 0:
            return "exhausted_theme"
        return "watch"

    def _rank_core_stocks(self, stocks: list[CoreStockEvidence]) -> list[RankedCoreStock]:
        ranked = [
            RankedCoreStock(
                rank=0,
                ts_code=stock.ts_code,
                name=stock.name,
                score=self._core_stock_score(stock),
                evidence=stock,
            )
            for stock in stocks
        ]
        ranked.sort(key=lambda item: item.score, reverse=True)
        return [
            RankedCoreStock(
                rank=index + 1,
                ts_code=stock.ts_code,
                name=stock.name,
                score=stock.score,
                evidence=stock.evidence,
            )
            for index, stock in enumerate(ranked)
        ]

    def _core_stock_score(self, stock: CoreStockEvidence) -> int:
        market_cap_score = self._clamp_decimal(
            stock.market_cap / Decimal("50000000000"),
            Decimal("0"),
            Decimal("1.5"),
        )
        turnover_score = self._clamp_decimal(stock.turnover_rate / Decimal("5"), Decimal("0"), Decimal("1"))
        score = (
            self._clamp_decimal(stock.multi_period_rs, Decimal("0"), Decimal("0.50")) * Decimal("60")
            + self._clamp_decimal(stock.amount_expansion, Decimal("0"), Decimal("3")) * Decimal("8")
            + self._clamp_decimal(stock.theme_profit_effect, Decimal("0"), Decimal("1")) * Decimal("20")
            + market_cap_score * Decimal("10")
            + turnover_score * Decimal("8")
        )
        return max(0, min(100, int(score)))

    def _clamp_decimal(self, value: Decimal, lower: Decimal, upper: Decimal) -> Decimal:
        return max(lower, min(upper, value))
