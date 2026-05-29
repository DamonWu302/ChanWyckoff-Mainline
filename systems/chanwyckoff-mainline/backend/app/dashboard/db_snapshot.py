from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dashboard.snapshot import DashboardSignalInput, OperationsDashboardBuilder
from app.models.market_data import DailyBar, IndexBar, Instrument, Theme, ThemeConstituent, ThemeSnapshot
from app.selection.market_regime import MarketBreadthEvidence, MarketIndexEvidence, MarketRegimeService
from app.selection.theme_strength import CoreStockEvidence, ThemeStrengthEvidence, ThemeStrengthService


class DbOperationsSnapshotSource:
    def __init__(self, session: Session) -> None:
        self.session = session

    def build(self, trade_date: date) -> dict[str, object] | None:
        shanghai = self._index_evidence("000001.SH", trade_date)
        all_a = self._index_evidence("000985.CSI", trade_date)
        themes = self._theme_evidence(trade_date)
        if shanghai is None or all_a is None or not themes:
            return None

        theme_strength = ThemeStrengthService().evaluate(
            trade_date=trade_date,
            themes=themes,
            core_stocks={
                theme.theme_code: self._core_stock_evidence(theme.theme_code, trade_date)
                for theme in themes
            },
        )
        market_regime = MarketRegimeService().evaluate(
            trade_date=trade_date,
            shanghai=shanghai,
            all_a=all_a,
            breadth=self._breadth(trade_date, theme_strength_count=len(theme_strength.themes)),
        )
        return OperationsDashboardBuilder().build(
            market_regime=market_regime,
            theme_strength=theme_strength,
            signals=self._signal_inputs(trade_date),
        )

    def _index_evidence(self, index_code: str, trade_date: date) -> MarketIndexEvidence | None:
        bars = list(
            self.session.scalars(
                select(IndexBar)
                .where(IndexBar.index_code == index_code, IndexBar.trade_date <= trade_date)
                .order_by(IndexBar.trade_date.desc())
                .limit(21)
            )
        )
        if not bars or bars[0].trade_date != trade_date:
            return None
        current = bars[0]
        previous = bars[1] if len(bars) > 1 else current
        return MarketIndexEvidence(
            index_code=index_code,
            close=current.close,
            ma20=self._average([bar.close for bar in bars[:20]]),
            pct_change=self._ratio(current.close - previous.close, previous.close),
            amount=current.amount or Decimal("0"),
            amount_ma20=self._average([bar.amount or Decimal("0") for bar in bars[:20]]),
        )

    def _theme_evidence(self, trade_date: date) -> list[ThemeStrengthEvidence]:
        snapshots = list(
            self.session.scalars(
                select(ThemeSnapshot)
                .join(Theme)
                .where(ThemeSnapshot.trade_date == trade_date, Theme.is_active.is_(True))
                .order_by(ThemeSnapshot.amount.desc().nullslast(), Theme.theme_code)
            )
        )
        return [self._theme_snapshot_evidence(snapshot, trade_date) for snapshot in snapshots]

    def _theme_snapshot_evidence(
        self,
        snapshot: ThemeSnapshot,
        trade_date: date,
    ) -> ThemeStrengthEvidence:
        history = list(
            self.session.scalars(
                select(ThemeSnapshot)
                .where(
                    ThemeSnapshot.theme_id == snapshot.theme_id,
                    ThemeSnapshot.trade_date <= trade_date,
                )
                .order_by(ThemeSnapshot.trade_date.desc())
                .limit(21)
            )
        )
        previous_amounts = [
            item.amount
            for item in history[1:21]
            if item.amount is not None and item.amount > 0
        ]
        amount_ratio_20 = self._ratio(
            snapshot.amount or Decimal("0"),
            self._average(previous_amounts) if previous_amounts else snapshot.amount or Decimal("0"),
        )
        return ThemeStrengthEvidence(
            theme_code=snapshot.theme.theme_code,
            theme_name=snapshot.theme.theme_name,
            rs_3=self._relative_strength(history, 3),
            rs_5=self._relative_strength(history, 5),
            rs_10=self._relative_strength(history, 10),
            rs_20=self._relative_strength(history, 20),
            amount_ratio_20=amount_ratio_20,
            rising_count=snapshot.rising_count or 0,
            limit_up_count=snapshot.limit_up_count or 0,
            new_high_count=snapshot.new_high_count or 0,
            resisted_in_weak_market=(snapshot.rising_count or 0) >= 25 and amount_ratio_20 >= Decimal("1.2"),
        )

    def _core_stock_evidence(self, theme_code: str, trade_date: date) -> list[CoreStockEvidence]:
        rows = list(
            self.session.execute(
                select(ThemeConstituent, Instrument, DailyBar)
                .join(Theme, ThemeConstituent.theme_id == Theme.id)
                .join(Instrument, ThemeConstituent.instrument_id == Instrument.id)
                .join(
                    DailyBar,
                    (DailyBar.instrument_id == Instrument.id)
                    & (DailyBar.trade_date == trade_date)
                    & (DailyBar.adjustment == "qfq"),
                )
                .where(
                    Theme.theme_code == theme_code,
                    ThemeConstituent.effective_date <= trade_date,
                    Instrument.is_active.is_(True),
                    Instrument.market_board == "main_board",
                )
            )
        )
        return [
            CoreStockEvidence(
                ts_code=instrument.ts_code,
                name=instrument.name,
                multi_period_rs=self._stock_relative_strength(instrument.id, trade_date),
                amount_expansion=self._stock_amount_expansion(instrument.id, trade_date),
                theme_profit_effect=Decimal("0.70") if constituent.is_primary else Decimal("0.45"),
                market_cap=bar.market_cap or Decimal("0"),
                turnover_rate=bar.turnover_rate or Decimal("0"),
            )
            for constituent, instrument, bar in rows
        ]

    def _breadth(self, trade_date: date, theme_strength_count: int) -> MarketBreadthEvidence:
        bars = list(
            self.session.scalars(
                select(DailyBar)
                .join(Instrument)
                .where(
                    DailyBar.trade_date == trade_date,
                    DailyBar.adjustment == "qfq",
                    Instrument.is_active.is_(True),
                    Instrument.market_board == "main_board",
                )
            )
        )
        rising_count = sum(1 for bar in bars if bar.close >= bar.open)
        falling_count = sum(1 for bar in bars if bar.close < bar.open)
        limit_down_count = sum(1 for bar in bars if bar.close <= bar.open * Decimal("0.90"))
        return MarketBreadthEvidence(
            rising_count=rising_count,
            falling_count=falling_count,
            limit_down_count=limit_down_count,
            strong_theme_count=theme_strength_count,
        )

    def _signal_inputs(self, _: date) -> list[DashboardSignalInput]:
        return []

    def _relative_strength(self, history: list[ThemeSnapshot], lookback: int) -> Decimal:
        if not history:
            return Decimal("0")
        current = history[0]
        if len(history) > lookback and current.close is not None and history[lookback].close:
            return self._ratio(current.close - history[lookback].close, history[lookback].close)
        return self._ratio(current.pct_change or Decimal("0"), Decimal("100"))

    def _stock_relative_strength(self, instrument_id: int, trade_date: date) -> Decimal:
        bars = list(
            self.session.scalars(
                select(DailyBar)
                .where(
                    DailyBar.instrument_id == instrument_id,
                    DailyBar.trade_date <= trade_date,
                    DailyBar.adjustment == "qfq",
                )
                .order_by(DailyBar.trade_date.desc())
                .limit(21)
            )
        )
        if len(bars) < 2:
            return Decimal("0")
        oldest = bars[-1]
        return self._ratio(bars[0].close - oldest.close, oldest.close)

    def _stock_amount_expansion(self, instrument_id: int, trade_date: date) -> Decimal:
        bars = list(
            self.session.scalars(
                select(DailyBar)
                .where(
                    DailyBar.instrument_id == instrument_id,
                    DailyBar.trade_date <= trade_date,
                    DailyBar.adjustment == "qfq",
                )
                .order_by(DailyBar.trade_date.desc())
                .limit(21)
            )
        )
        if not bars:
            return Decimal("0")
        previous_amounts = [bar.amount for bar in bars[1:21] if bar.amount > 0]
        denominator = self._average(previous_amounts) if previous_amounts else bars[0].amount
        return self._ratio(bars[0].amount, denominator)

    def _average(self, values: list[Decimal]) -> Decimal:
        if not values:
            return Decimal("0")
        return sum(values, Decimal("0")) / Decimal(len(values))

    def _ratio(self, numerator: Decimal, denominator: Decimal | None) -> Decimal:
        if denominator is None or denominator == 0:
            return Decimal("0")
        return numerator / denominator
