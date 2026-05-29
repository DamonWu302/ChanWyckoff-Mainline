from datetime import date
from decimal import Decimal

from app.ingestion.tdx_snapshot_provider import TdxCsvSnapshotProvider


def test_tdx_csv_snapshot_provider_loads_local_supplement_file(tmp_path) -> None:
    path = tmp_path / "tdx_snapshot.csv"
    path.write_text(
        "ts_code,amount,turnover_rate,market_cap,raw_payload\n"
        "600519.SH,2987654321.00,1.23,2450000000000.00,\"{source:tdx}\"\n",
        encoding="utf-8",
    )
    provider = TdxCsvSnapshotProvider()

    dataset = provider.load_snapshot_file(str(path), date(2026, 5, 25))

    assert len(dataset.snapshots) == 1
    snapshot = dataset.snapshots[0]
    assert snapshot["ts_code"] == "600519.SH"
    assert snapshot["trade_date"] == date(2026, 5, 25)
    assert snapshot["amount"] == Decimal("2987654321.00")
    assert snapshot["turnover_rate"] == Decimal("1.23")
    assert snapshot["market_cap"] == Decimal("2450000000000.00")
    assert snapshot["source_file"] == str(path)


def test_tdx_csv_snapshot_provider_treats_blank_optional_values_as_none(tmp_path) -> None:
    path = tmp_path / "tdx_snapshot.csv"
    path.write_text(
        "ts_code,amount,turnover_rate,market_cap\n"
        "600519.SH,,,\n",
        encoding="utf-8",
    )
    provider = TdxCsvSnapshotProvider()

    dataset = provider.load_snapshot_file(str(path), date(2026, 5, 25))

    assert dataset.snapshots[0]["amount"] is None
    assert dataset.snapshots[0]["turnover_rate"] is None
    assert dataset.snapshots[0]["market_cap"] is None
