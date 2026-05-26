from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.review import SignalLlmReview, SignalReviewEvent, SignalReviewRecord


@dataclass(frozen=True, slots=True)
class ManualReviewPayload:
    signal_uid: str
    ts_code: str
    signal_time: datetime
    rule_state: str
    suggested_action: str
    manual_status: str
    note: str
    failure_reason: str | None
    return_pct: Decimal | None
    max_drawdown_pct: Decimal | None
    holding_bars: int | None


@dataclass(frozen=True, slots=True)
class LlmReviewPayload:
    signal_uid: str
    provider: str
    model: str
    background_summary: str
    feature_summary: str
    forecast_summary: str
    failure_type: str | None
    attempted_rule_state: str | None = None
    attempted_action: str | None = None


class SignalReviewService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def record_manual_review(self, payload: ManualReviewPayload) -> SignalReviewRecord:
        record = self.get_record(payload.signal_uid)
        if record is None:
            record = SignalReviewRecord(
                signal_uid=payload.signal_uid,
                ts_code=payload.ts_code,
                signal_time=payload.signal_time,
                rule_state=payload.rule_state,
                suggested_action=payload.suggested_action,
                manual_status=payload.manual_status,
            )
            self.session.add(record)
        else:
            record.ts_code = payload.ts_code
            record.signal_time = payload.signal_time
            record.manual_status = payload.manual_status

        record.failure_reason = payload.failure_reason
        record.return_pct = payload.return_pct
        record.max_drawdown_pct = payload.max_drawdown_pct
        record.holding_bars = payload.holding_bars
        record.events.append(
            SignalReviewEvent(
                manual_status=payload.manual_status,
                note=payload.note,
                failure_reason=payload.failure_reason,
            )
        )
        self.session.commit()
        self.session.refresh(record)
        return record

    def attach_llm_review(self, payload: LlmReviewPayload) -> SignalLlmReview:
        record = self.get_record(payload.signal_uid)
        if record is None:
            raise ValueError(f"Signal review record does not exist: {payload.signal_uid}")

        review = SignalLlmReview(
            record_id=record.id,
            provider=payload.provider,
            model=payload.model,
            background_summary=payload.background_summary,
            feature_summary=payload.feature_summary,
            forecast_summary=payload.forecast_summary,
            failure_type=payload.failure_type,
            attempted_rule_state=payload.attempted_rule_state,
            attempted_action=payload.attempted_action,
        )
        self.session.add(review)
        self.session.commit()
        self.session.refresh(review)
        return review

    def get_record(self, signal_uid: str) -> SignalReviewRecord | None:
        return self.session.scalar(
            select(SignalReviewRecord)
            .where(SignalReviewRecord.signal_uid == signal_uid)
            .options(
                selectinload(SignalReviewRecord.events),
                selectinload(SignalReviewRecord.llm_reviews),
            )
        )
