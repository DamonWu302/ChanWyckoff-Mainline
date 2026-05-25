from dataclasses import dataclass
from datetime import date

from app.ingestion.market_data import (
    MarketDataIngestionService,
    ThemeConstituentPayload,
    ThemePayload,
    ThemeSnapshotPayload,
    UpsertResult,
)
from app.ingestion.providers import AkshareThemeProvider


@dataclass(frozen=True, slots=True)
class ThemeImportResult:
    themes: UpsertResult
    constituents: UpsertResult
    snapshots: UpsertResult


class ThemeIngestionPipeline:
    def __init__(
        self,
        ingestion_service: MarketDataIngestionService,
        provider: AkshareThemeProvider,
    ) -> None:
        self.ingestion_service = ingestion_service
        self.provider = provider

    def import_trade_date(self, trade_date: date) -> ThemeImportResult:
        dataset = self.provider.fetch_trade_date(trade_date)
        themes = self.ingestion_service.upsert_themes(
            [ThemePayload(**record) for record in dataset.themes]
        )
        constituents = self.ingestion_service.upsert_theme_constituents(
            [ThemeConstituentPayload(**record) for record in dataset.constituents]
        )
        snapshots = self.ingestion_service.upsert_theme_snapshots(
            [ThemeSnapshotPayload(**record) for record in dataset.snapshots]
        )
        return ThemeImportResult(themes=themes, constituents=constituents, snapshots=snapshots)
