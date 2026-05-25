from dataclasses import dataclass
from datetime import date

from app.ingestion.market_data import (
    DailyBarPayload,
    InstrumentPayload,
    IntradayBarPayload,
    MarketDataIngestionService,
    UpsertResult,
)
from app.ingestion.providers import TickFlowProvider


@dataclass(frozen=True, slots=True)
class MarketBarsImportResult:
    instruments: UpsertResult
    daily_bars: UpsertResult
    intraday_bars: UpsertResult


class MarketBarsIngestionPipeline:
    def __init__(
        self,
        ingestion_service: MarketDataIngestionService,
        provider: TickFlowProvider,
    ) -> None:
        self.ingestion_service = ingestion_service
        self.provider = provider

    def import_bars(
        self,
        ts_code: str,
        start_date: date,
        end_date: date,
        adjustment: str,
        include_30m: bool,
    ) -> MarketBarsImportResult:
        dataset = self.provider.fetch_bars(
            ts_code=ts_code,
            start_date=start_date,
            end_date=end_date,
            adjustment=adjustment,
            include_30m=include_30m,
        )
        instruments = self.ingestion_service.upsert_instruments(
            [InstrumentPayload(**record) for record in dataset.instruments]
        )
        daily_bars = self.ingestion_service.upsert_daily_bars(
            [DailyBarPayload(**record) for record in dataset.daily_bars]
        )
        intraday_bars = self.ingestion_service.upsert_intraday_bars(
            [IntradayBarPayload(**record) for record in dataset.intraday_bars]
        )
        return MarketBarsImportResult(
            instruments=instruments,
            daily_bars=daily_bars,
            intraday_bars=intraday_bars,
        )
