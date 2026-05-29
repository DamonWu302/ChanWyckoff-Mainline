from datetime import date
from decimal import Decimal

from app.ingestion.akshare_theme_provider import AkshareHttpThemeProvider


def test_akshare_theme_provider_fetches_themes_constituents_and_snapshots() -> None:
    requests: list[tuple[str, dict[str, str]]] = []

    def fake_get(path: str, params: dict[str, str]) -> dict[str, object]:
        requests.append((path, params))
        if path == "/themes":
            return {
                "themes": [
                    {
                        "theme_code": "BK1234",
                        "theme_name": "机器人",
                        "theme_type": "concept",
                        "is_active": True,
                    }
                ]
            }
        if path == "/themes/constituents":
            return {
                "constituents": [
                    {
                        "theme_code": "BK1234",
                        "ts_code": "600001.SH",
                        "weight": "0.92",
                        "reason": "趋势容量核心",
                        "is_primary": True,
                    }
                ]
            }
        if path == "/themes/snapshots":
            return {
                "snapshots": [
                    {
                        "theme_code": "BK1234",
                        "close": "1020.5",
                        "pct_change": "0.035",
                        "amount": "9765432100.00",
                        "rising_count": 18,
                        "limit_up_count": 4,
                        "new_high_count": 6,
                    }
                ]
            }
        raise AssertionError(path)

    provider = AkshareHttpThemeProvider(
        base_url="https://eastmoney.example.test",
        get_json=fake_get,
    )

    dataset = provider.fetch_trade_date(date(2026, 5, 25))

    assert requests == [
        ("/themes", {"trade_date": "2026-05-25"}),
        ("/themes/constituents", {"trade_date": "2026-05-25"}),
        ("/themes/snapshots", {"trade_date": "2026-05-25"}),
    ]
    assert dataset.themes[0]["source"] == "akshare"
    assert dataset.themes[0]["theme_name"] == "机器人"
    assert dataset.constituents[0]["effective_date"] == date(2026, 5, 25)
    assert dataset.constituents[0]["weight"] == Decimal("0.92")
    assert dataset.snapshots[0]["trade_date"] == date(2026, 5, 25)
    assert dataset.snapshots[0]["amount"] == Decimal("9765432100.00")


def test_akshare_theme_provider_handles_blank_optional_values() -> None:
    def fake_get(path: str, params: dict[str, str]) -> dict[str, object]:
        if path == "/themes":
            return {"themes": []}
        if path == "/themes/constituents":
            return {"constituents": [{"theme_code": "BK1234", "ts_code": "600001.SH", "weight": ""}]}
        if path == "/themes/snapshots":
            return {"snapshots": [{"theme_code": "BK1234", "amount": ""}]}
        raise AssertionError(path)

    provider = AkshareHttpThemeProvider(
        base_url="https://eastmoney.example.test",
        get_json=fake_get,
    )

    dataset = provider.fetch_trade_date(date(2026, 5, 25))

    assert dataset.constituents[0]["weight"] is None
    assert dataset.snapshots[0]["amount"] is None
