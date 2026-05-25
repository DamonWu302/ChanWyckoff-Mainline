from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.market_data import DailyBar, Instrument


@dataclass(frozen=True, slots=True)
class StockPoolCriteria:
    min_amount: Decimal
    min_market_cap: Decimal
    min_turnover_rate: Decimal
    max_downtrend_days: int


@dataclass(frozen=True, slots=True)
class StockPoolCandidate:
    ts_code: str
    name: str
    amount: Decimal
    market_cap: Decimal
    turnover_rate: Decimal


@dataclass(frozen=True, slots=True)
class StockPoolResult:
    trade_date: date
    candidates: list[StockPoolCandidate] = field(default_factory=list)
    excluded: dict[str, str] = field(default_factory=dict)


class StockPoolService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def build_tradeable_pool(
        self,
        trade_date: date,
        criteria: StockPoolCriteria,
    ) -> StockPoolResult:
        instruments = self.session.scalars(select(Instrument).order_by(Instrument.ts_code)).all()
        candidates: list[StockPoolCandidate] = []
        excluded: dict[str, str] = {}

        for instrument in instruments:
            reason = self._exclusion_reason(instrument, trade_date, criteria)
            if reason is not None:
                excluded[instrument.ts_code] = reason
                continue

            latest_bar = self._latest_bar(instrument.id, trade_date)
            if latest_bar is None:
                excluded[instrument.ts_code] = "missing_daily_bar"
                continue

            candidates.append(
                StockPoolCandidate(
                    ts_code=instrument.ts_code,
                    name=instrument.name,
                    amount=latest_bar.amount,
                    market_cap=latest_bar.market_cap or Decimal("0"),
                    turnover_rate=latest_bar.turnover_rate or Decimal("0"),
                )
            )

        return StockPoolResult(trade_date=trade_date, candidates=candidates, excluded=excluded)

    def _exclusion_reason(
        self,
        instrument: Instrument,
        trade_date: date,
        criteria: StockPoolCriteria,
    ) -> str | None:
        if not instrument.is_active or instrument.delist_date is not None:
            return "inactive_or_delisted"
        if instrument.is_st:
            return "st_or_risk"
        if instrument.market_board != "main_board":
            return "non_main_board"

        latest_bar = self._latest_bar(instrument.id, trade_date)
        if latest_bar is None:
            return "missing_daily_bar"
        if latest_bar.amount < criteria.min_amount:
            return "insufficient_amount"
        if (latest_bar.market_cap or Decimal("0")) < criteria.min_market_cap:
            return "insufficient_market_cap"
        if (latest_bar.turnover_rate or Decimal("0")) < criteria.min_turnover_rate:
            return "insufficient_turnover"
        if self._has_one_way_downtrend(instrument.id, trade_date, criteria.max_downtrend_days):
            return "one_way_downtrend"
        return None

    def _latest_bar(self, instrument_id: int, trade_date: date) -> DailyBar | None:
        return self.session.scalar(
            select(DailyBar)
            .where(DailyBar.instrument_id == instrument_id, DailyBar.trade_date == trade_date)
            .order_by(DailyBar.trade_date.desc())
        )

    def _has_one_way_downtrend(
        self,
        instrument_id: int,
        trade_date: date,
        max_downtrend_days: int,
    ) -> bool:
        lookback_start = trade_date - timedelta(days=max_downtrend_days + 3)
        bars = list(
            self.session.scalars(
                select(DailyBar)
                .where(
                    DailyBar.instrument_id == instrument_id,
                    DailyBar.trade_date >= lookback_start,
                    DailyBar.trade_date <= trade_date,
                )
                .order_by(DailyBar.trade_date)
            )
        )
        if len(bars) <= max_downtrend_days:
            return False

        consecutive_down = 0
        previous_close: Decimal | None = None
        for bar in bars:
            if previous_close is not None and bar.close < previous_close:
                consecutive_down += 1
            else:
                consecutive_down = 0
            previous_close = bar.close

        return consecutive_down >= max_downtrend_days
