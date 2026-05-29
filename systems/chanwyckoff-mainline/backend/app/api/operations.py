from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.dashboard.snapshot import build_operations_snapshot
from app.db.session import get_db


router = APIRouter(tags=["operations"])


@router.get("/market-regime")
def get_market_regime(
    trade_date: date | None = None,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    snapshot = _operations_snapshot(trade_date, db)
    return snapshot["market_regime"]


@router.get("/themes/mainlines")
def get_mainlines(
    trade_date: date | None = None,
    db: Session = Depends(get_db),
) -> list[dict[str, object]]:
    snapshot = _operations_snapshot(trade_date, db)
    return snapshot["mainlines"]


@router.get("/themes/{theme_code}/core-stocks")
def get_core_stocks(
    theme_code: str,
    trade_date: date | None = None,
    db: Session = Depends(get_db),
) -> list[dict[str, object]]:
    snapshot = _operations_snapshot(trade_date, db)
    for theme in snapshot["mainlines"]:
        if theme.get("theme_code") == theme_code:
            return theme["core_stocks"]
    raise HTTPException(status_code=404, detail="Theme mainline not found")


def _operations_snapshot(trade_date: date | None, db: Session) -> dict[str, object]:
    if trade_date is not None:
        from app.dashboard.db_snapshot import DbOperationsSnapshotSource

        try:
            snapshot = DbOperationsSnapshotSource(db).build(trade_date)
        except SQLAlchemyError:
            snapshot = None
        if snapshot is not None:
            return snapshot
    return build_operations_snapshot(trade_date=trade_date)
