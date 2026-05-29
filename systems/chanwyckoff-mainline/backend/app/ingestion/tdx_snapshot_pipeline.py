from datetime import date

from app.ingestion.market_data import (
    MarketDataIngestionService,
    TdxDailySnapshotPayload,
    UpsertResult,
)
from app.ingestion.providers import TdxSnapshotProvider


class TdxSnapshotIngestionPipeline:
    def __init__(
        self,
        ingestion_service: MarketDataIngestionService,
        provider: TdxSnapshotProvider,
    ) -> None:
        self.ingestion_service = ingestion_service
        self.provider = provider

    def import_snapshot_file(self, path: str, trade_date: date) -> UpsertResult:
        dataset = self.provider.load_snapshot_file(path, trade_date)
        return self.ingestion_service.upsert_tdx_daily_snapshots(
            [TdxDailySnapshotPayload(**record) for record in dataset.snapshots]
        )
