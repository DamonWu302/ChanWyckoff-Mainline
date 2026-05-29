from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.selection.stock_pool import StockPoolCandidate, StockPoolCriteria, StockPoolService


router = APIRouter(prefix="/stock-pool", tags=["stock-pool"])


@router.get("")
def get_stock_pool(
    trade_date: date,
    min_amount: Decimal = Decimal("100000000"),
    min_market_cap: Decimal = Decimal("5000000000"),
    min_turnover_rate: Decimal = Decimal("1.0"),
    max_downtrend_days: int = 5,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    criteria = StockPoolCriteria(
        min_amount=min_amount,
        min_market_cap=min_market_cap,
        min_turnover_rate=min_turnover_rate,
        max_downtrend_days=max_downtrend_days,
    )
    result = StockPoolService(db).build_tradeable_pool(trade_date, criteria)

    return {
        "trade_date": result.trade_date.isoformat(),
        "criteria": {
            "min_amount": str(criteria.min_amount),
            "min_market_cap": str(criteria.min_market_cap),
            "min_turnover_rate": str(criteria.min_turnover_rate),
            "max_downtrend_days": criteria.max_downtrend_days,
        },
        "candidates": [_candidate_to_dict(candidate) for candidate in result.candidates],
        "excluded": result.excluded,
    }


def _candidate_to_dict(candidate: StockPoolCandidate) -> dict[str, str]:
    return {
        "ts_code": candidate.ts_code,
        "name": candidate.name,
        "amount": _decimal_places(candidate.amount, "0.0001"),
        "market_cap": _decimal_places(candidate.market_cap, "0.0001"),
        "turnover_rate": _decimal_places(candidate.turnover_rate, "0.0001"),
    }


def _decimal_places(value: Decimal, places: str) -> str:
    return str(value.quantize(Decimal(places)))
