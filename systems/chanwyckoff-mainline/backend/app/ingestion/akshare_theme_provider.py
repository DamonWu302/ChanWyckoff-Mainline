from collections.abc import Callable, Mapping
from datetime import date
from decimal import Decimal
from typing import Any

import httpx

from app.ingestion.providers import ProviderRecord, ThemeProviderDataset


JsonGet = Callable[[str, dict[str, str]], Mapping[str, Any]]


class AkshareHttpThemeProvider:
    source = "akshare"

    def __init__(
        self,
        base_url: str,
        get_json: JsonGet | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._get_json = get_json or self._http_get_json

    def fetch_trade_date(self, trade_date: date) -> ThemeProviderDataset:
        params = {"trade_date": trade_date.isoformat()}
        themes_payload = self._get_json("/themes", params)
        constituents_payload = self._get_json("/themes/constituents", params)
        snapshots_payload = self._get_json("/themes/snapshots", params)
        return ThemeProviderDataset(
            themes=[self._theme_record(item) for item in self._items(themes_payload, "themes")],
            constituents=[
                self._constituent_record(item, trade_date)
                for item in self._items(constituents_payload, "constituents")
            ],
            snapshots=[
                self._snapshot_record(item, trade_date)
                for item in self._items(snapshots_payload, "snapshots")
            ],
        )

    def _http_get_json(self, path: str, params: dict[str, str]) -> Mapping[str, Any]:
        with httpx.Client(base_url=self.base_url, timeout=30.0) as client:
            response = client.get(path, params=params)
            response.raise_for_status()
            payload = response.json()
        if not isinstance(payload, Mapping):
            raise ValueError("AkShare theme response must be a JSON object")
        return payload

    def _items(self, payload: Mapping[str, Any], key: str) -> list[Mapping[str, Any]]:
        items = payload.get(key, [])
        if not isinstance(items, list):
            raise ValueError(f"AkShare {key} must be a list")
        return [item for item in items if isinstance(item, Mapping)]

    def _theme_record(self, item: Mapping[str, Any]) -> ProviderRecord:
        return {
            "source": self.source,
            "theme_code": str(item["theme_code"]),
            "theme_name": str(item["theme_name"]),
            "theme_type": str(item.get("theme_type", "concept")),
            "is_active": bool(item.get("is_active", True)),
        }

    def _constituent_record(self, item: Mapping[str, Any], trade_date: date) -> ProviderRecord:
        return {
            "theme_source": self.source,
            "theme_code": str(item["theme_code"]),
            "ts_code": str(item["ts_code"]),
            "effective_date": trade_date,
            "weight": self._optional_decimal(item.get("weight")),
            "reason": self._optional_str(item.get("reason")),
            "is_primary": bool(item.get("is_primary", False)),
        }

    def _snapshot_record(self, item: Mapping[str, Any], trade_date: date) -> ProviderRecord:
        return {
            "theme_source": self.source,
            "theme_code": str(item["theme_code"]),
            "trade_date": trade_date,
            "close": self._optional_decimal(item.get("close")),
            "pct_change": self._optional_decimal(item.get("pct_change")),
            "amount": self._optional_decimal(item.get("amount")),
            "rising_count": self._optional_int(item.get("rising_count")),
            "limit_up_count": self._optional_int(item.get("limit_up_count")),
            "new_high_count": self._optional_int(item.get("new_high_count")),
            "source": self.source,
        }

    def _optional_decimal(self, value: object) -> Decimal | None:
        if value is None or str(value).strip() == "":
            return None
        return Decimal(str(value).strip())

    def _optional_int(self, value: object) -> int | None:
        if value is None or str(value).strip() == "":
            return None
        return int(value)

    def _optional_str(self, value: object) -> str | None:
        if value is None or str(value).strip() == "":
            return None
        return str(value)
