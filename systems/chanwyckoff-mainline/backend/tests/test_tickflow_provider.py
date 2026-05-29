from datetime import date, datetime, timezone
from decimal import Decimal

from app.core.config import Settings
from app.ingestion.tickflow_provider import TickFlowHttpProvider, create_tickflow_provider


def test_tickflow_provider_fetches_daily_and_30m_qfq_dataset() -> None:
    requests: list[tuple[str, dict[str, str], dict[str, str]]] = []

    def fake_get(path: str, params: dict[str, str], headers: dict[str, str]) -> dict[str, object]:
        requests.append((path, params, headers))
        if path == "/stock/bars":
            if params["frequency"] == "1d":
                return {
                    "instrument": {
                        "symbol": "600519",
                        "exchange": "SH",
                        "name": "贵州茅台",
                        "market_board": "main_board",
                        "is_active": True,
                        "is_st": False,
                    },
                    "bars": [
                        {
                            "ts_code": "600519.SH",
                            "trade_date": "2026-05-25",
                            "open": "1598.00",
                            "high": "1620.00",
                            "low": "1588.00",
                            "close": "1610.00",
                            "volume": 12345678,
                            "amount": "1987654321.00",
                        }
                    ],
                }
            return {
                "bars": [
                    {
                        "ts_code": "600519.SH",
                        "bar_time": "2026-05-25T10:00:00+00:00",
                        "open": "1601.00",
                        "high": "1608.00",
                        "low": "1599.00",
                        "close": "1605.00",
                        "volume": 123400,
                        "amount": "19876543.21",
                    }
                ]
            }
        raise AssertionError(path)

    provider = TickFlowHttpProvider(
        base_url="https://api.example.test",
        api_key="secret-token",
        get_json=fake_get,
    )

    dataset = provider.fetch_bars(
        ts_code="600519.SH",
        start_date=date(2026, 5, 25),
        end_date=date(2026, 5, 25),
        adjustment="qfq",
        include_30m=True,
    )

    assert len(requests) == 2
    assert requests[0] == (
        "/stock/bars",
        {
            "ts_code": "600519.SH",
            "start_date": "2026-05-25",
            "end_date": "2026-05-25",
            "adjustment": "qfq",
            "frequency": "1d",
        },
        {"Authorization": "Bearer secret-token"},
    )
    assert dataset.instruments[0]["name"] == "贵州茅台"
    assert dataset.daily_bars[0]["trade_date"] == date(2026, 5, 25)
    assert dataset.daily_bars[0]["close"] == Decimal("1610.00")
    assert dataset.intraday_bars[0]["bar_time"] == datetime(2026, 5, 25, 10, 0, tzinfo=timezone.utc)
    assert dataset.intraday_bars[0]["frequency"] == "30m"


def test_tickflow_provider_can_skip_30m_fetch() -> None:
    requests: list[dict[str, str]] = []

    def fake_get(path: str, params: dict[str, str], headers: dict[str, str]) -> dict[str, object]:
        requests.append(params)
        return {
            "instrument": {
                "symbol": "600519",
                "exchange": "SH",
                "name": "贵州茅台",
                "market_board": "main_board",
                "is_active": True,
                "is_st": False,
            },
            "bars": [],
        }

    provider = TickFlowHttpProvider(
        base_url="https://api.example.test",
        api_key=None,
        get_json=fake_get,
    )

    dataset = provider.fetch_bars(
        ts_code="600519.SH",
        start_date=date(2026, 5, 25),
        end_date=date(2026, 5, 25),
        adjustment="qfq",
        include_30m=False,
    )

    assert len(requests) == 1
    assert requests[0]["frequency"] == "1d"
    assert dataset.intraday_bars == []


def test_tickflow_provider_fetches_index_bars() -> None:
    requests: list[tuple[str, dict[str, str], dict[str, str]]] = []

    def fake_get(
        path: str,
        params: dict[str, str],
        headers: dict[str, str],
    ) -> dict[str, object]:
        requests.append((path, params, headers))
        return {
            "bars": [
                {
                    "index_code": "000001.SH",
                    "index_name": "上证指数",
                    "trade_date": "2026-05-25",
                    "open": "3120.10",
                    "high": "3160.20",
                    "low": "3108.30",
                    "close": "3150.40",
                    "volume": 123456789,
                    "amount": "456789012345.00",
                }
            ]
        }

    provider = TickFlowHttpProvider(
        base_url="https://api.example.test",
        api_key="secret-token",
        get_json=fake_get,
    )

    dataset = provider.fetch_index_bars(
        "000001.SH",
        date(2026, 5, 25),
        date(2026, 5, 26),
        adjustment="none",
    )

    assert requests == [
        (
            "/index/bars",
            {
                "index_code": "000001.SH",
                "start_date": "2026-05-25",
                "end_date": "2026-05-26",
                "adjustment": "none",
                "frequency": "1d",
            },
            {"Authorization": "Bearer secret-token"},
        )
    ]
    assert dataset.index_bars[0]["index_name"] == "上证指数"
    assert dataset.index_bars[0]["trade_date"] == date(2026, 5, 25)
    assert dataset.index_bars[0]["amount"] == Decimal("456789012345.00")
    assert dataset.index_bars[0]["source"] == "tickflow"


def test_tickflow_provider_factory_uses_settings_without_exposing_secret() -> None:
    settings = Settings(
        tickflow_base_url="https://api.example.test/",
        tickflow_api_key="secret-token",
    )

    provider = create_tickflow_provider(settings)

    assert provider.base_url == "https://api.example.test"
    assert provider.api_key == "secret-token"
