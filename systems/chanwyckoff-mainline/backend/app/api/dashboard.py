from fastapi import APIRouter

from app.dashboard.snapshot import build_operations_snapshot


router = APIRouter(tags=["dashboard"])


@router.get("/dashboard")
def get_dashboard() -> dict[str, object]:
    return build_operations_snapshot()
