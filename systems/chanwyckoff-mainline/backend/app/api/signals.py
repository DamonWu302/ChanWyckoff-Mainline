from datetime import date

from fastapi import APIRouter, HTTPException

from app.signals.detail import SignalDetailService, detail_to_dict


router = APIRouter(prefix="/signals", tags=["signals"])


@router.get("")
def list_signals(trade_date: date | None = None) -> list[dict[str, object]]:
    from app.dashboard.snapshot import build_operations_snapshot

    snapshot = build_operations_snapshot(trade_date=trade_date)
    return snapshot["signals"]


@router.get("/{ts_code}/detail")
def get_signal_detail(ts_code: str) -> dict[str, object]:
    detail = SignalDetailService().get_detail(ts_code)
    if detail is None:
        raise HTTPException(status_code=404, detail="Signal detail not found")
    return detail_to_dict(detail)
