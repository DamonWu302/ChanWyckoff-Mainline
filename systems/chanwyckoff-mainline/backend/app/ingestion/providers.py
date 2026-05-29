from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Protocol, TypeAlias


ProviderValue: TypeAlias = str | bool | int | date | datetime | Decimal | None
ProviderRecord: TypeAlias = Mapping[str, ProviderValue]


@dataclass(frozen=True, slots=True)
class ThemeProviderDataset:
    themes: list[ProviderRecord]
    constituents: list[ProviderRecord]
    snapshots: list[ProviderRecord]


@dataclass(frozen=True, slots=True)
class MarketBarsDataset:
    instruments: list[ProviderRecord]
    daily_bars: list[ProviderRecord]
    intraday_bars: list[ProviderRecord]


@dataclass(frozen=True, slots=True)
class IndexBarsDataset:
    index_bars: list[ProviderRecord]


@dataclass(frozen=True, slots=True)
class TdxSnapshotDataset:
    snapshots: list[ProviderRecord]


class TickFlowProvider(Protocol):
    source: str

    def fetch_bars(
        self,
        ts_code: str,
        start_date: date,
        end_date: date,
        adjustment: str,
        include_30m: bool,
    ) -> MarketBarsDataset:
        """Fetch qfq daily and optional 30m bars for one instrument."""

    def fetch_index_bars(
        self,
        index_code: str,
        start_date: date,
        end_date: date,
        adjustment: str,
    ) -> IndexBarsDataset:
        """Fetch daily index bars used by market-regime evidence."""


class AkshareThemeProvider(Protocol):
    source: str

    def fetch_trade_date(self, trade_date: date) -> ThemeProviderDataset:
        """Fetch concept themes, constituents and theme snapshots for one trade date."""


class TdxSnapshotProvider(Protocol):
    source: str

    def load_snapshot_file(self, path: str, trade_date: date) -> TdxSnapshotDataset:
        """Load local TongDaXin supplement snapshots without making it a hard dependency."""
