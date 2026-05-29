from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.dashboard.snapshot import build_operations_snapshot
from app.db.session import get_db


router = APIRouter(tags=["dashboard"])


@router.get("/dashboard")
def get_dashboard(
    trade_date: date | None = None,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    if trade_date is not None:
        from app.dashboard.db_snapshot import DbOperationsSnapshotSource

        try:
            snapshot = DbOperationsSnapshotSource(db).build(trade_date)
        except SQLAlchemyError:
            snapshot = None
        if snapshot is not None:
            return snapshot
    return build_operations_snapshot(trade_date=trade_date)
