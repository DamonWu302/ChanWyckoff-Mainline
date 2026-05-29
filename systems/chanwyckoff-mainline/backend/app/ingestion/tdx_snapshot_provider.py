import csv
from datetime import date
from decimal import Decimal
from pathlib import Path

from app.ingestion.providers import ProviderRecord, TdxSnapshotDataset


class TdxCsvSnapshotProvider:
    source = "tdx"

    def load_snapshot_file(self, path: str, trade_date: date) -> TdxSnapshotDataset:
        source_path = Path(path)
        with source_path.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        return TdxSnapshotDataset(
            snapshots=[
                self._snapshot_record(row, trade_date, str(source_path))
                for row in rows
                if row.get("ts_code")
            ]
        )

    def _snapshot_record(
        self,
        row: dict[str, str | None],
        trade_date: date,
        source_file: str,
    ) -> ProviderRecord:
        return {
            "ts_code": str(row["ts_code"]).strip(),
            "trade_date": trade_date,
            "amount": self._optional_decimal(row.get("amount")),
            "turnover_rate": self._optional_decimal(row.get("turnover_rate")),
            "market_cap": self._optional_decimal(row.get("market_cap")),
            "raw_payload": row.get("raw_payload"),
            "source_file": source_file,
        }

    def _optional_decimal(self, value: str | None) -> Decimal | None:
        if value is None or value.strip() == "":
            return None
        return Decimal(value.strip())
