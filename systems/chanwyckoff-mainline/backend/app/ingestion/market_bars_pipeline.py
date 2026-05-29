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

    def import_symbol_batch(
        self,
        ts_codes: list[str],
        start_date: date,
        end_date: date,
        adjustment: str,
        include_30m: bool,
    ) -> MarketBarsImportResult:
        result = MarketBarsImportResult(
            instruments=UpsertResult(created=0, updated=0),
            daily_bars=UpsertResult(created=0, updated=0),
            intraday_bars=UpsertResult(created=0, updated=0),
        )
        for ts_code in ts_codes:
            item_result = self.import_bars(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
                adjustment=adjustment,
                include_30m=include_30m,
            )
            result = MarketBarsImportResult(
                instruments=self._merge_result(result.instruments, item_result.instruments),
                daily_bars=self._merge_result(result.daily_bars, item_result.daily_bars),
                intraday_bars=self._merge_result(result.intraday_bars, item_result.intraday_bars),
            )
        return result

    def _merge_result(self, left: UpsertResult, right: UpsertResult) -> UpsertResult:
        return UpsertResult(
            created=left.created + right.created,
            updated=left.updated + right.updated,
        )
