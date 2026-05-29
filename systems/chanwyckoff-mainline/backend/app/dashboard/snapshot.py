from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from app.selection.market_regime import MarketRegimeResult
from app.selection.theme_strength import (
    CoreStockEvidence,
    RankedCoreStock,
    RankedTheme,
    ThemeStrengthEvidence,
    ThemeStrengthResult,
)


@dataclass(frozen=True, slots=True)
class DashboardSignalInput:
    ts_code: str
    name: str
    theme: str
    state: str
    score: int
    suggested_action: str
    amount: Decimal
    signal_time: datetime
    structure_evidence: str
    volume_price_evidence: str
    wyckoff_forecast: str


class OperationsDashboardBuilder:
    def build(
        self,
        market_regime: MarketRegimeResult,
        theme_strength: ThemeStrengthResult,
        signals: list[DashboardSignalInput],
    ) -> dict[str, object]:
        themes = self._top_themes(theme_strength.themes)
        return {
            "trade_date": market_regime.trade_date.isoformat(),
            "market_regime": {
                "state": market_regime.regime,
                "attack_allowed": not market_regime.suppress_new_signals,
                "suppress_new_signals": market_regime.suppress_new_signals,
                "recommended_exposure_pct": self._recommended_exposure(market_regime),
                "evidence": [str(value) for value in market_regime.evidence.values()],
            },
            "mainlines": [self._theme_to_dict(theme) for theme in themes],
            "signals": [self._signal_to_dict(signal, market_regime) for signal in signals],
            "filters": {
                "themes": sorted({signal.theme for signal in signals}),
                "states": ["proto_3buy", "confirmed_3buy", "failed_3buy"],
                "score_floor": [40, 60, 80],
            },
        }

    def _theme_to_dict(self, theme: RankedTheme) -> dict[str, object]:
        return {
            "theme": theme.theme_name,
            "label": theme.label,
            "strength_score": theme.score,
            "amount_expansion": f"{theme.evidence.amount_ratio_20:.2f}x",
            "core_stocks": [
                {
                    "rank": stock.rank,
                    "ts_code": stock.ts_code,
                    "name": stock.name,
                    "score": stock.score,
                }
                for stock in theme.core_stocks[:5]
            ],
        }

    def _signal_to_dict(
        self,
        signal: DashboardSignalInput,
        market_regime: MarketRegimeResult,
    ) -> dict[str, object]:
        return {
            "ts_code": signal.ts_code,
            "name": signal.name,
            "theme": signal.theme,
            "state": signal.state,
            "score": signal.score,
            "suggested_action": self._signal_action(signal, market_regime),
            "amount": int(signal.amount),
            "signal_time": signal.signal_time.isoformat(),
            "evidence": {
                "structure": signal.structure_evidence,
                "volume_price": signal.volume_price_evidence,
                "wyckoff_forecast": signal.wyckoff_forecast,
            },
        }

    def _signal_action(
        self,
        signal: DashboardSignalInput,
        market_regime: MarketRegimeResult,
    ) -> str:
        if market_regime.suppress_new_signals and signal.suggested_action != "filter":
            return "observe"
        return signal.suggested_action

    def _top_themes(self, themes: list[RankedTheme]) -> list[RankedTheme]:
        return [
            theme
            for theme in themes
            if theme.label in {"confirmed_mainline", "emerging_leader", "resistant_theme"}
        ][:5]

    def _recommended_exposure(self, market_regime: MarketRegimeResult) -> int:
        if market_regime.regime == "risk_on":
            return 70
        if market_regime.regime == "risk_off":
            return 10
        return 45


def build_operations_snapshot(trade_date: date | None = None) -> dict[str, object]:
    trade_date = trade_date or date.today()
    return OperationsDashboardBuilder().build(
        market_regime=_sample_market_regime(trade_date),
        theme_strength=ThemeStrengthResult(trade_date=trade_date, themes=_sample_themes()),
        signals=_sample_signals(),
    )


def _sample_market_regime(trade_date: date) -> MarketRegimeResult:
    return MarketRegimeResult(
        trade_date=trade_date,
        regime="neutral",
        score=55,
        evidence={
            "index": "index_repair_without_full_risk_on",
            "breadth": "breadth_improving_but_not_expanding",
            "gate": "confirmed_mainline_required",
        },
        suppress_new_signals=False,
    )


def _sample_themes() -> list[RankedTheme]:
    robotics = RankedTheme(
        theme_code="BK1234",
        theme_name="机器人",
        score=88,
        label="confirmed_mainline",
        evidence=_theme_evidence("BK1234", "机器人", Decimal("1.62")),
        core_stocks=[
            _core_stock(1, "600001.SH", "机器人核心 Alpha", 91),
            _core_stock(2, "600002.SH", "机器人跟踪 Delta", 83),
        ],
    )
    cpo = RankedTheme(
        theme_code="BK5678",
        theme_name="CPO",
        score=79,
        label="emerging_leader",
        evidence=_theme_evidence("BK5678", "CPO", Decimal("1.31")),
        core_stocks=[_core_stock(1, "600010.SH", "CPO 核心 Beta", 86)],
    )
    return [robotics, cpo]


def _theme_evidence(theme_code: str, theme_name: str, amount_ratio: Decimal) -> ThemeStrengthEvidence:
    return ThemeStrengthEvidence(
        theme_code=theme_code,
        theme_name=theme_name,
        rs_3=Decimal("0.12"),
        rs_5=Decimal("0.15"),
        rs_10=Decimal("0.18"),
        rs_20=Decimal("0.20"),
        amount_ratio_20=amount_ratio,
        rising_count=18,
        limit_up_count=4,
        new_high_count=6,
        resisted_in_weak_market=True,
    )


def _core_stock(rank: int, ts_code: str, name: str, score: int) -> RankedCoreStock:
    return RankedCoreStock(
        rank=rank,
        ts_code=ts_code,
        name=name,
        score=score,
        evidence=CoreStockEvidence(
            ts_code=ts_code,
            name=name,
            multi_period_rs=Decimal("0.28"),
            amount_expansion=Decimal("2.1"),
            theme_profit_effect=Decimal("0.72"),
            market_cap=Decimal("65000000000"),
            turnover_rate=Decimal("4.8"),
        ),
    )


def _sample_signals() -> list[DashboardSignalInput]:
    signal_time = datetime.fromisoformat("2026-05-26T14:00:00+00:00")
    return [
        DashboardSignalInput(
            ts_code="600001.SH",
            name="机器人核心 Alpha",
            theme="机器人",
            state="confirmed_3buy",
            score=86,
            suggested_action="upgrade_position",
            amount=Decimal("200000000"),
            signal_time=signal_time,
            structure_evidence="30m_platform_upper_breakout",
            volume_price_evidence="breakout_expansion_pullback_shrinking",
            wyckoff_forecast="continuation_expected",
        ),
        DashboardSignalInput(
            ts_code="600010.SH",
            name="CPO 核心 Beta",
            theme="CPO",
            state="proto_3buy",
            score=78,
            suggested_action="light_position",
            amount=Decimal("160000000"),
            signal_time=signal_time,
            structure_evidence="close_above_platform_upper",
            volume_price_evidence="breakout_volume_confirmed",
            wyckoff_forecast="wait_pullback_confirmation",
        ),
        DashboardSignalInput(
            ts_code="600020.SH",
            name="算力观察 Gamma",
            theme="算力",
            state="failed_3buy",
            score=41,
            suggested_action="filter",
            amount=Decimal("90000000"),
            signal_time=signal_time,
            structure_evidence="fell_back_inside_platform",
            volume_price_evidence="supply_returned_on_volume",
            wyckoff_forecast="supply_returned",
        ),
    ]
