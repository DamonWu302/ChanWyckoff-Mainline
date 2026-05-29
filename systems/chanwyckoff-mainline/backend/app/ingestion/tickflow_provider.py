from collections.abc import Callable, Mapping
from datetime import date, datetime
from decimal import Decimal
from typing import Any

import httpx

from app.ingestion.providers import MarketBarsDataset, ProviderRecord


JsonGet = Callable[[str, dict[str, str], dict[str, str]], Mapping[str, Any]]


def create_tickflow_provider(settings: object) -> "TickFlowHttpProvider":
    return TickFlowHttpProvider(
        base_url=str(getattr(settings, "tickflow_base_url")),
        api_key=getattr(settings, "tickflow_api_key"),
    )


class TickFlowHttpProvider:
    source = "tickflow"

    def __init__(
        self,
        base_url: str,
        api_key: str | None,
        get_json: JsonGet | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._get_json = get_json or self._http_get_json

    def fetch_bars(
        self,
        ts_code: str,
        start_date: date,
        end_date: date,
        adjustment: str,
        include_30m: bool,
    ) -> MarketBarsDataset:
        daily_payload = self._fetch_frequency(ts_code, start_date, end_date, adjustment, "1d")
        intraday_payload = (
            self._fetch_frequency(ts_code, start_date, end_date, adjustment, "30m")
            if include_30m
            else {"bars": []}
        )
        instrument = daily_payload.get("instrument")
        instruments = [self._instrument_record(instrument)] if isinstance(instrument, Mapping) else []
        return MarketBarsDataset(
            instruments=instruments,
            daily_bars=[
                self._daily_bar_record(item, adjustment)
                for item in self._bars_from_payload(daily_payload)
            ],
            intraday_bars=[
                self._intraday_bar_record(item, adjustment)
                for item in self._bars_from_payload(intraday_payload)
            ],
        )

    def _fetch_frequency(
        self,
        ts_code: str,
        start_date: date,
        end_date: date,
        adjustment: str,
        frequency: str,
    ) -> Mapping[str, Any]:
        return self._get_json(
            "/stock/bars",
            {
                "ts_code": ts_code,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "adjustment": adjustment,
                "frequency": frequency,
            },
            self._headers(),
        )

    def _http_get_json(
        self,
        path: str,
        params: dict[str, str],
        headers: dict[str, str],
    ) -> Mapping[str, Any]:
        with httpx.Client(base_url=self.base_url, timeout=30.0) as client:
            response = client.get(path, params=params, headers=headers)
            response.raise_for_status()
            payload = response.json()
        if not isinstance(payload, Mapping):
            raise ValueError("TickFlow response must be a JSON object")
        return payload

    def _headers(self) -> dict[str, str]:
        if self.api_key is None:
            return {}
        return {"Authorization": f"Bearer {self.api_key}"}

    def _bars_from_payload(self, payload: Mapping[str, Any]) -> list[Mapping[str, Any]]:
        bars = payload.get("bars", [])
        if not isinstance(bars, list):
            raise ValueError("TickFlow bars must be a list")
        return [item for item in bars if isinstance(item, Mapping)]

    def _instrument_record(self, item: Mapping[str, Any]) -> ProviderRecord:
        return {
            "symbol": str(item["symbol"]),
            "exchange": str(item["exchange"]),
            "name": str(item["name"]),
            "market_board": str(item.get("market_board", "main_board")),
            "industry": self._optional_str(item.get("industry")),
            "list_date": self._optional_date(item.get("list_date")),
            "delist_date": self._optional_date(item.get("delist_date")),
            "is_active": bool(item.get("is_active", True)),
            "is_st": bool(item.get("is_st", False)),
        }

    def _daily_bar_record(self, item: Mapping[str, Any], adjustment: str) -> ProviderRecord:
        return {
            "ts_code": str(item["ts_code"]),
            "trade_date": self._date(item["trade_date"]),
            "adjustment": adjustment,
            "open": self._decimal(item["open"]),
            "high": self._decimal(item["high"]),
            "low": self._decimal(item["low"]),
            "close": self._decimal(item["close"]),
            "volume": int(item["volume"]),
            "amount": self._decimal(item["amount"]),
            "turnover_rate": self._optional_decimal(item.get("turnover_rate")),
            "market_cap": self._optional_decimal(item.get("market_cap")),
            "source": self.source,
        }

    def _intraday_bar_record(self, item: Mapping[str, Any], adjustment: str) -> ProviderRecord:
        return {
            "ts_code": str(item["ts_code"]),
            "bar_time": self._datetime(item["bar_time"]),
            "frequency": "30m",
            "adjustment": adjustment,
            "open": self._decimal(item["open"]),
            "high": self._decimal(item["high"]),
            "low": self._decimal(item["low"]),
            "close": self._decimal(item["close"]),
            "volume": int(item["volume"]),
            "amount": self._decimal(item["amount"]),
            "source": self.source,
        }

    def _date(self, value: object) -> date:
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        if isinstance(value, str):
            return date.fromisoformat(value)
        raise ValueError(f"Unsupported TickFlow date value: {value!r}")

    def _optional_date(self, value: object) -> date | None:
        if value is None:
            return None
        return self._date(value)

    def _datetime(self, value: object) -> datetime:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            return datetime.fromisoformat(value)
        raise ValueError(f"Unsupported TickFlow datetime value: {value!r}")

    def _decimal(self, value: object) -> Decimal:
        return Decimal(str(value))

    def _optional_decimal(self, value: object) -> Decimal | None:
        if value is None:
            return None
        return self._decimal(value)

    def _optional_str(self, value: object) -> str | None:
        if value is None:
            return None
        return str(value)
