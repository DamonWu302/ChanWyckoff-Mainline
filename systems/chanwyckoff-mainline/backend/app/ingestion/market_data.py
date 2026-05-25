from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.market_data import (
    DailyBar,
    Instrument,
    IntradayBar,
    IndexBar,
    TdxDailySnapshot,
    Theme,
    ThemeConstituent,
    ThemeSnapshot,
    TradingCalendar,
)


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


@dataclass(frozen=True, slots=True)
class IntradayBarPayload:
    ts_code: str
    bar_time: datetime
    frequency: str
    adjustment: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    amount: Decimal
    source: str


@dataclass(frozen=True, slots=True)
class TradingCalendarPayload:
    exchange: str
    trade_date: date
    is_open: bool
    previous_trade_date: date | None = None
    next_trade_date: date | None = None


@dataclass(frozen=True, slots=True)
class IndexBarPayload:
    index_code: str
    index_name: str
    trade_date: date
    adjustment: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    source: str
    volume: int | None = None
    amount: Decimal | None = None


@dataclass(frozen=True, slots=True)
class TdxDailySnapshotPayload:
    ts_code: str
    trade_date: date
    amount: Decimal | None = None
    turnover_rate: Decimal | None = None
    market_cap: Decimal | None = None
    raw_payload: str | None = None
    source_file: str | None = None


@dataclass(frozen=True, slots=True)
class ThemePayload:
    source: str
    theme_code: str
    theme_name: str
    theme_type: str
    is_active: bool


@dataclass(frozen=True, slots=True)
class ThemeConstituentPayload:
    theme_source: str
    theme_code: str
    ts_code: str
    effective_date: date
    weight: Decimal | None = None
    reason: str | None = None
    is_primary: bool = False


@dataclass(frozen=True, slots=True)
class ThemeSnapshotPayload:
    theme_source: str
    theme_code: str
    trade_date: date
    source: str
    close: Decimal | None = None
    pct_change: Decimal | None = None
    amount: Decimal | None = None
    rising_count: int | None = None
    limit_up_count: int | None = None
    new_high_count: int | None = None


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

    def upsert_intraday_bars(self, payloads: list[IntradayBarPayload]) -> UpsertResult:
        created = 0
        updated = 0

        for payload in payloads:
            instrument = self.get_instrument(payload.ts_code)
            if instrument is None:
                raise ValueError(f"Instrument {payload.ts_code} must exist before importing bars")

            intraday_bar = self.get_intraday_bar(
                payload.ts_code,
                payload.bar_time,
                payload.frequency,
                payload.adjustment,
            )
            if intraday_bar is None:
                self.session.add(
                    IntradayBar(
                        instrument_id=instrument.id,
                        bar_time=payload.bar_time,
                        frequency=payload.frequency,
                        adjustment=payload.adjustment,
                        open=payload.open,
                        high=payload.high,
                        low=payload.low,
                        close=payload.close,
                        volume=payload.volume,
                        amount=payload.amount,
                        source=payload.source,
                    )
                )
                created += 1
                continue

            intraday_bar.open = payload.open
            intraday_bar.high = payload.high
            intraday_bar.low = payload.low
            intraday_bar.close = payload.close
            intraday_bar.volume = payload.volume
            intraday_bar.amount = payload.amount
            intraday_bar.source = payload.source
            updated += 1

        self.session.flush()
        return UpsertResult(created=created, updated=updated)

    def upsert_trading_calendars(
        self, payloads: list[TradingCalendarPayload]
    ) -> UpsertResult:
        created = 0
        updated = 0

        for payload in payloads:
            calendar = self.get_trading_calendar(payload.exchange, payload.trade_date)
            if calendar is None:
                self.session.add(
                    TradingCalendar(
                        exchange=payload.exchange,
                        trade_date=payload.trade_date,
                        is_open=payload.is_open,
                        previous_trade_date=payload.previous_trade_date,
                        next_trade_date=payload.next_trade_date,
                    )
                )
                created += 1
                continue

            calendar.is_open = payload.is_open
            calendar.previous_trade_date = payload.previous_trade_date
            calendar.next_trade_date = payload.next_trade_date
            updated += 1

        self.session.flush()
        return UpsertResult(created=created, updated=updated)

    def upsert_index_bars(self, payloads: list[IndexBarPayload]) -> UpsertResult:
        created = 0
        updated = 0

        for payload in payloads:
            index_bar = self.get_index_bar(payload.index_code, payload.trade_date, payload.adjustment)
            if index_bar is None:
                self.session.add(
                    IndexBar(
                        index_code=payload.index_code,
                        index_name=payload.index_name,
                        trade_date=payload.trade_date,
                        adjustment=payload.adjustment,
                        open=payload.open,
                        high=payload.high,
                        low=payload.low,
                        close=payload.close,
                        volume=payload.volume,
                        amount=payload.amount,
                        source=payload.source,
                    )
                )
                created += 1
                continue

            index_bar.index_name = payload.index_name
            index_bar.open = payload.open
            index_bar.high = payload.high
            index_bar.low = payload.low
            index_bar.close = payload.close
            index_bar.volume = payload.volume
            index_bar.amount = payload.amount
            index_bar.source = payload.source
            updated += 1

        self.session.flush()
        return UpsertResult(created=created, updated=updated)

    def upsert_tdx_daily_snapshots(
        self, payloads: list[TdxDailySnapshotPayload]
    ) -> UpsertResult:
        created = 0
        updated = 0

        for payload in payloads:
            snapshot = self.get_tdx_daily_snapshot(payload.ts_code, payload.trade_date)
            if snapshot is None:
                self.session.add(
                    TdxDailySnapshot(
                        ts_code=payload.ts_code,
                        trade_date=payload.trade_date,
                        amount=payload.amount,
                        turnover_rate=payload.turnover_rate,
                        market_cap=payload.market_cap,
                        raw_payload=payload.raw_payload,
                        source_file=payload.source_file,
                    )
                )
                created += 1
                continue

            snapshot.amount = payload.amount
            snapshot.turnover_rate = payload.turnover_rate
            snapshot.market_cap = payload.market_cap
            snapshot.raw_payload = payload.raw_payload
            snapshot.source_file = payload.source_file
            updated += 1

        self.session.flush()
        return UpsertResult(created=created, updated=updated)

    def upsert_themes(self, payloads: list[ThemePayload]) -> UpsertResult:
        created = 0
        updated = 0

        for payload in payloads:
            theme = self.get_theme(payload.source, payload.theme_code)
            if theme is None:
                self.session.add(
                    Theme(
                        source=payload.source,
                        theme_code=payload.theme_code,
                        theme_name=payload.theme_name,
                        theme_type=payload.theme_type,
                        is_active=payload.is_active,
                    )
                )
                created += 1
                continue

            theme.theme_name = payload.theme_name
            theme.theme_type = payload.theme_type
            theme.is_active = payload.is_active
            updated += 1

        self.session.flush()
        return UpsertResult(created=created, updated=updated)

    def upsert_theme_constituents(
        self, payloads: list[ThemeConstituentPayload]
    ) -> UpsertResult:
        created = 0
        updated = 0

        for payload in payloads:
            theme = self.get_theme(payload.theme_source, payload.theme_code)
            if theme is None:
                raise ValueError(
                    f"Theme {payload.theme_source}:{payload.theme_code} must exist before "
                    "importing constituents"
                )
            instrument = self.get_instrument(payload.ts_code)
            if instrument is None:
                raise ValueError(
                    f"Instrument {payload.ts_code} must exist before importing constituents"
                )

            constituent = self.get_theme_constituent(
                payload.theme_source,
                payload.theme_code,
                payload.ts_code,
                payload.effective_date,
            )
            if constituent is None:
                self.session.add(
                    ThemeConstituent(
                        theme_id=theme.id,
                        instrument_id=instrument.id,
                        effective_date=payload.effective_date,
                        weight=payload.weight,
                        reason=payload.reason,
                        is_primary=payload.is_primary,
                    )
                )
                created += 1
                continue

            constituent.weight = payload.weight
            constituent.reason = payload.reason
            constituent.is_primary = payload.is_primary
            updated += 1

        self.session.flush()
        return UpsertResult(created=created, updated=updated)

    def upsert_theme_snapshots(self, payloads: list[ThemeSnapshotPayload]) -> UpsertResult:
        created = 0
        updated = 0

        for payload in payloads:
            theme = self.get_theme(payload.theme_source, payload.theme_code)
            if theme is None:
                raise ValueError(
                    f"Theme {payload.theme_source}:{payload.theme_code} must exist before "
                    "importing snapshots"
                )

            snapshot = self.get_theme_snapshot(
                payload.theme_source,
                payload.theme_code,
                payload.trade_date,
            )
            if snapshot is None:
                self.session.add(
                    ThemeSnapshot(
                        theme_id=theme.id,
                        trade_date=payload.trade_date,
                        close=payload.close,
                        pct_change=payload.pct_change,
                        amount=payload.amount,
                        rising_count=payload.rising_count,
                        limit_up_count=payload.limit_up_count,
                        new_high_count=payload.new_high_count,
                        source=payload.source,
                    )
                )
                created += 1
                continue

            snapshot.close = payload.close
            snapshot.pct_change = payload.pct_change
            snapshot.amount = payload.amount
            snapshot.rising_count = payload.rising_count
            snapshot.limit_up_count = payload.limit_up_count
            snapshot.new_high_count = payload.new_high_count
            snapshot.source = payload.source
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

    def get_intraday_bar(
        self,
        ts_code: str,
        bar_time: datetime,
        frequency: str,
        adjustment: str,
    ) -> IntradayBar | None:
        return self.session.scalar(
            select(IntradayBar)
            .join(Instrument)
            .where(
                Instrument.ts_code == ts_code,
                IntradayBar.bar_time == bar_time,
                IntradayBar.frequency == frequency,
                IntradayBar.adjustment == adjustment,
            )
        )

    def count_intraday_bars(self) -> int:
        return self.session.scalar(select(func.count()).select_from(IntradayBar)) or 0

    def get_trading_calendar(self, exchange: str, trade_date: date) -> TradingCalendar | None:
        return self.session.scalar(
            select(TradingCalendar).where(
                TradingCalendar.exchange == exchange,
                TradingCalendar.trade_date == trade_date,
            )
        )

    def count_trading_calendars(self) -> int:
        return self.session.scalar(select(func.count()).select_from(TradingCalendar)) or 0

    def get_index_bar(
        self,
        index_code: str,
        trade_date: date,
        adjustment: str,
    ) -> IndexBar | None:
        return self.session.scalar(
            select(IndexBar).where(
                IndexBar.index_code == index_code,
                IndexBar.trade_date == trade_date,
                IndexBar.adjustment == adjustment,
            )
        )

    def count_index_bars(self) -> int:
        return self.session.scalar(select(func.count()).select_from(IndexBar)) or 0

    def get_tdx_daily_snapshot(
        self,
        ts_code: str,
        trade_date: date,
    ) -> TdxDailySnapshot | None:
        return self.session.scalar(
            select(TdxDailySnapshot).where(
                TdxDailySnapshot.ts_code == ts_code,
                TdxDailySnapshot.trade_date == trade_date,
            )
        )

    def count_tdx_daily_snapshots(self) -> int:
        return self.session.scalar(select(func.count()).select_from(TdxDailySnapshot)) or 0

    def get_theme(self, source: str, theme_code: str) -> Theme | None:
        return self.session.scalar(
            select(Theme).where(Theme.source == source, Theme.theme_code == theme_code)
        )

    def count_themes(self) -> int:
        return self.session.scalar(select(func.count()).select_from(Theme)) or 0

    def get_theme_constituent(
        self,
        theme_source: str,
        theme_code: str,
        ts_code: str,
        effective_date: date,
    ) -> ThemeConstituent | None:
        return self.session.scalar(
            select(ThemeConstituent)
            .join(Theme)
            .join(Instrument)
            .where(
                Theme.source == theme_source,
                Theme.theme_code == theme_code,
                Instrument.ts_code == ts_code,
                ThemeConstituent.effective_date == effective_date,
            )
        )

    def count_theme_constituents(self) -> int:
        return self.session.scalar(select(func.count()).select_from(ThemeConstituent)) or 0

    def get_theme_snapshot(
        self,
        theme_source: str,
        theme_code: str,
        trade_date: date,
    ) -> ThemeSnapshot | None:
        return self.session.scalar(
            select(ThemeSnapshot)
            .join(Theme)
            .where(
                Theme.source == theme_source,
                Theme.theme_code == theme_code,
                ThemeSnapshot.trade_date == trade_date,
            )
        )

    def count_theme_snapshots(self) -> int:
        return self.session.scalar(select(func.count()).select_from(ThemeSnapshot)) or 0
