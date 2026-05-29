from collections.abc import Iterator
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.ingestion.market_data import MarketDataIngestionService
from app.ingestion.providers import TdxSnapshotDataset
from app.ingestion.tdx_snapshot_pipeline import TdxSnapshotIngestionPipeline


@pytest.fixture()
def db_session() -> Iterator[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    with SessionLocal() as session:
        yield session


class FakeTdxSnapshotProvider:
    source = "tdx"

    def __init__(self) -> None:
        self.requests: list[tuple[str, date]] = []

    def load_snapshot_file(self, path: str, trade_date: date) -> TdxSnapshotDataset:
        self.requests.append((path, trade_date))
        return TdxSnapshotDataset(
            snapshots=[
                {
                    "ts_code": "600001.SH",
                    "trade_date": trade_date,
                    "amount": Decimal("123456789.00"),
                    "turnover_rate": Decimal("1.23"),
                    "market_cap": Decimal("9876543210.00"),
                    "raw_payload": "{\"rank\":1}",
                    "source_file": path,
                }
            ]
        )


def test_tdx_snapshot_pipeline_imports_snapshot_file_idempotently(db_session: Session) -> None:
    service = MarketDataIngestionService(db_session)
    provider = FakeTdxSnapshotProvider()
    pipeline = TdxSnapshotIngestionPipeline(service, provider)

    first_result = pipeline.import_snapshot_file("/data/tdx/20260525.csv", date(2026, 5, 25))
    second_result = pipeline.import_snapshot_file("/data/tdx/20260525.csv", date(2026, 5, 25))

    assert provider.requests == [
        ("/data/tdx/20260525.csv", date(2026, 5, 25)),
        ("/data/tdx/20260525.csv", date(2026, 5, 25)),
    ]
    assert first_result.created == 1
    assert second_result.updated == 1
    assert service.count_tdx_daily_snapshots() == 1
