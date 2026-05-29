from datetime import date

from app.ingestion.market_data import (
    IndexBarPayload,
    MarketDataIngestionService,
    UpsertResult,
)
from app.ingestion.providers import TickFlowProvider


class IndexBarsIngestionPipeline:
    def __init__(
        self,
        ingestion_service: MarketDataIngestionService,
        provider: TickFlowProvider,
    ) -> None:
        self.ingestion_service = ingestion_service
        self.provider = provider

    def import_index_bars(
        self,
        index_code: str,
        start_date: date,
        end_date: date,
        adjustment: str,
    ) -> UpsertResult:
        dataset = self.provider.fetch_index_bars(
            index_code=index_code,
            start_date=start_date,
            end_date=end_date,
            adjustment=adjustment,
        )
        return self.ingestion_service.upsert_index_bars(
            [IndexBarPayload(**record) for record in dataset.index_bars]
        )
