from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.review import SignalLlmReview, SignalReviewEvent, SignalReviewRecord
from app.review.signal_review import LlmReviewPayload, ManualReviewPayload, SignalReviewService


router = APIRouter(prefix="/reviews", tags=["reviews"])


class ManualReviewRequest(BaseModel):
    signal_uid: str
    ts_code: str
    signal_time: datetime
    rule_state: str
    suggested_action: str
    manual_status: str
    note: str
    failure_reason: str | None = None
    return_pct: Decimal | None = None
    max_drawdown_pct: Decimal | None = None
    holding_bars: int | None = None


class LlmReviewRequest(BaseModel):
    provider: str
    model: str
    background_summary: str
    feature_summary: str
    forecast_summary: str
    failure_type: str | None = None
    attempted_rule_state: str | None = None
    attempted_action: str | None = None


@router.post("/manual")
def record_manual_review(
    payload: ManualReviewRequest,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    record = SignalReviewService(db).record_manual_review(
        ManualReviewPayload(
            signal_uid=payload.signal_uid,
            ts_code=payload.ts_code,
            signal_time=payload.signal_time,
            rule_state=payload.rule_state,
            suggested_action=payload.suggested_action,
            manual_status=payload.manual_status,
            note=payload.note,
            failure_reason=payload.failure_reason,
            return_pct=payload.return_pct,
            max_drawdown_pct=payload.max_drawdown_pct,
            holding_bars=payload.holding_bars,
        )
    )
    return _record_to_dict(record)


@router.get("/stats/failures")
def get_failure_distribution(db: Session = Depends(get_db)) -> dict[str, object]:
    distribution = SignalReviewService(db).failure_distribution()
    return {
        "manual_failure_reasons": distribution.manual_failure_reasons,
        "llm_failure_types": distribution.llm_failure_types,
        "total_failed_records": distribution.total_failed_records,
    }


@router.post("/{signal_uid}/llm")
def attach_llm_review(
    signal_uid: str,
    payload: LlmReviewRequest,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        review = SignalReviewService(db).attach_llm_review(
            LlmReviewPayload(
                signal_uid=signal_uid,
                provider=payload.provider,
                model=payload.model,
                background_summary=payload.background_summary,
                feature_summary=payload.feature_summary,
                forecast_summary=payload.forecast_summary,
                failure_type=payload.failure_type,
                attempted_rule_state=payload.attempted_rule_state,
                attempted_action=payload.attempted_action,
            )
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _llm_review_to_dict(review)


@router.get("/{signal_uid}")
def get_review(signal_uid: str, db: Session = Depends(get_db)) -> dict[str, object]:
    record = SignalReviewService(db).get_record(signal_uid)
    if record is None:
        raise HTTPException(status_code=404, detail="Signal review record not found")
    return _record_to_dict(record)


def _record_to_dict(record: SignalReviewRecord) -> dict[str, object]:
    return {
        "id": record.id,
        "signal_uid": record.signal_uid,
        "ts_code": record.ts_code,
        "signal_time": record.signal_time.isoformat(),
        "rule_state": record.rule_state,
        "suggested_action": record.suggested_action,
        "manual_status": record.manual_status,
        "failure_reason": record.failure_reason,
        "return_pct": _decimal(record.return_pct),
        "max_drawdown_pct": _decimal(record.max_drawdown_pct),
        "holding_bars": record.holding_bars,
        "events": [_event_to_dict(event) for event in record.events],
        "llm_reviews": [_llm_review_to_dict(review) for review in record.llm_reviews],
    }


def _event_to_dict(event: SignalReviewEvent) -> dict[str, object]:
    return {
        "id": event.id,
        "manual_status": event.manual_status,
        "note": event.note,
        "failure_reason": event.failure_reason,
    }


def _llm_review_to_dict(review: SignalLlmReview) -> dict[str, object]:
    return {
        "id": review.id,
        "provider": review.provider,
        "model": review.model,
        "background_summary": review.background_summary,
        "feature_summary": review.feature_summary,
        "forecast_summary": review.forecast_summary,
        "failure_type": review.failure_type,
        "attempted_rule_state": review.attempted_rule_state,
        "attempted_action": review.attempted_action,
    }


def _decimal(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return f"{value:.6f}"
