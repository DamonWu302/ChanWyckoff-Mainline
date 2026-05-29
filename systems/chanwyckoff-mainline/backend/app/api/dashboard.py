from datetime import date

from fastapi import APIRouter

from app.dashboard.snapshot import build_operations_snapshot


router = APIRouter(tags=["dashboard"])


@router.get("/dashboard")
def get_dashboard(trade_date: date | None = None) -> dict[str, object]:
    return build_operations_snapshot(trade_date=trade_date)
