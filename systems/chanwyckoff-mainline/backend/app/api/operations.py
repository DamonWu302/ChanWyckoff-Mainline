from fastapi import APIRouter

from app.dashboard.snapshot import build_operations_snapshot


router = APIRouter(tags=["operations"])


@router.get("/market-regime")
def get_market_regime() -> dict[str, object]:
    snapshot = build_operations_snapshot()
    return snapshot["market_regime"]


@router.get("/themes/mainlines")
def get_mainlines() -> list[dict[str, object]]:
    snapshot = build_operations_snapshot()
    return snapshot["mainlines"]
