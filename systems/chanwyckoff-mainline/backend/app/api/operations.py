from datetime import date

from fastapi import APIRouter

from app.dashboard.snapshot import build_operations_snapshot


router = APIRouter(tags=["operations"])


@router.get("/market-regime")
def get_market_regime(trade_date: date | None = None) -> dict[str, object]:
    snapshot = build_operations_snapshot(trade_date=trade_date)
    return snapshot["market_regime"]


@router.get("/themes/mainlines")
def get_mainlines(trade_date: date | None = None) -> list[dict[str, object]]:
    snapshot = build_operations_snapshot(trade_date=trade_date)
    return snapshot["mainlines"]
