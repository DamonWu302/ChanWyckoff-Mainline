from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.market_data import DailyBar, Instrument


@dataclass(frozen=True, slots=True)
class InstrumentPayload:
    symbol: str
    exchange: str
    name: str
    market_board: str
    is_active: bool
    is_st: bool
    industry: str | None = None
    list_date: date | None = None
    delist_date: date | None = None

    @property
    def ts_code(self) -> str:
        return f"{self.symbol}.{self.exchange}"


@dataclass(frozen=True, slots=True)
class UpsertResult:
    created: int
    updated: int


@dataclass(frozen=True, slots=True)
class DailyBarPayload:
    ts_code: str
    trade_date: date
    adjustment: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    amount: Decimal
    source: str
    turnover_rate: Decimal | None = None
    market_cap: Decimal | None = None


class MarketDataIngestionService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert_instruments(self, payloads: list[InstrumentPayload]) -> UpsertResult:
        created = 0
        updated = 0

        for payload in payloads:
            instrument = self.get_instrument(payload.ts_code)
            if instrument is None:
                self.session.add(
                    Instrument(
                        ts_code=payload.ts_code,
                        symbol=payload.symbol,
                        exchange=payload.exchange,
                        name=payload.name,
                        market_board=payload.market_board,
                        industry=payload.industry,
                        list_date=payload.list_date,
                        delist_date=payload.delist_date,
                        is_active=payload.is_active,
                        is_st=payload.is_st,
                    )
                )
                created += 1
                continue

            instrument.name = payload.name
            instrument.market_board = payload.market_board
            instrument.industry = payload.industry
            instrument.list_date = payload.list_date
            instrument.delist_date = payload.delist_date
            instrument.is_active = payload.is_active
            instrument.is_st = payload.is_st
            updated += 1

        self.session.flush()
        return UpsertResult(created=created, updated=updated)

    def upsert_daily_bars(self, payloads: list[DailyBarPayload]) -> UpsertResult:
        created = 0
        updated = 0

        for payload in payloads:
            instrument = self.get_instrument(payload.ts_code)
            if instrument is None:
                raise ValueError(f"Instrument {payload.ts_code} must exist before importing bars")

            daily_bar = self.get_daily_bar(payload.ts_code, payload.trade_date, payload.adjustment)
            if daily_bar is None:
                self.session.add(
                    DailyBar(
                        instrument_id=instrument.id,
                        trade_date=payload.trade_date,
                        adjustment=payload.adjustment,
                        open=payload.open,
                        high=payload.high,
                        low=payload.low,
                        close=payload.close,
                        volume=payload.volume,
                        amount=payload.amount,
                        turnover_rate=payload.turnover_rate,
                        market_cap=payload.market_cap,
                        source=payload.source,
                    )
                )
                created += 1
                continue

            daily_bar.open = payload.open
            daily_bar.high = payload.high
            daily_bar.low = payload.low
            daily_bar.close = payload.close
            daily_bar.volume = payload.volume
            daily_bar.amount = payload.amount
            daily_bar.turnover_rate = payload.turnover_rate
            daily_bar.market_cap = payload.market_cap
            daily_bar.source = payload.source
            updated += 1

        self.session.flush()
        return UpsertResult(created=created, updated=updated)

    def get_instrument(self, ts_code: str) -> Instrument | None:
        return self.session.scalar(select(Instrument).where(Instrument.ts_code == ts_code))

    def count_instruments(self) -> int:
        return self.session.scalar(select(func.count()).select_from(Instrument)) or 0

    def get_daily_bar(self, ts_code: str, trade_date: date, adjustment: str) -> DailyBar | None:
        return self.session.scalar(
            select(DailyBar)
            .join(Instrument)
            .where(
                Instrument.ts_code == ts_code,
                DailyBar.trade_date == trade_date,
                DailyBar.adjustment == adjustment,
            )
        )

    def count_daily_bars(self) -> int:
        return self.session.scalar(select(func.count()).select_from(DailyBar)) or 0
