from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class SignalReviewRecord(TimestampMixin, Base):
    __tablename__ = "signal_review_records"
    __table_args__ = (
        UniqueConstraint("signal_uid", name="uq_signal_review_records_signal_uid"),
        Index("ix_signal_review_records_ts_code", "ts_code"),
        Index("ix_signal_review_records_manual_status", "manual_status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    signal_uid: Mapped[str] = mapped_column(String(96), nullable=False)
    ts_code: Mapped[str] = mapped_column(String(16), nullable=False)
    signal_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    rule_state: Mapped[str] = mapped_column(String(32), nullable=False)
    suggested_action: Mapped[str] = mapped_column(String(32), nullable=False)
    manual_status: Mapped[str] = mapped_column(String(32), nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(String(96))
    return_pct: Mapped[Decimal | None] = mapped_column(Numeric(12, 6))
    max_drawdown_pct: Mapped[Decimal | None] = mapped_column(Numeric(12, 6))
    holding_bars: Mapped[int | None] = mapped_column(Integer)

    events: Mapped[list["SignalReviewEvent"]] = relationship(
        back_populates="record",
        cascade="all, delete-orphan",
        order_by="SignalReviewEvent.id",
    )
    llm_reviews: Mapped[list["SignalLlmReview"]] = relationship(
        back_populates="record",
        cascade="all, delete-orphan",
        order_by="SignalLlmReview.id",
    )


class SignalReviewEvent(TimestampMixin, Base):
    __tablename__ = "signal_review_events"
    __table_args__ = (Index("ix_signal_review_events_manual_status", "manual_status"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    record_id: Mapped[int] = mapped_column(ForeignKey("signal_review_records.id"), nullable=False)
    manual_status: Mapped[str] = mapped_column(String(32), nullable=False)
    note: Mapped[str] = mapped_column(Text, nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(String(96))

    record: Mapped[SignalReviewRecord] = relationship(back_populates="events")


class SignalLlmReview(TimestampMixin, Base):
    __tablename__ = "signal_llm_reviews"
    __table_args__ = (Index("ix_signal_llm_reviews_failure_type", "failure_type"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    record_id: Mapped[int] = mapped_column(ForeignKey("signal_review_records.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    model: Mapped[str] = mapped_column(String(64), nullable=False)
    background_summary: Mapped[str] = mapped_column(Text, nullable=False)
    feature_summary: Mapped[str] = mapped_column(Text, nullable=False)
    forecast_summary: Mapped[str] = mapped_column(Text, nullable=False)
    failure_type: Mapped[str | None] = mapped_column(String(96))
    attempted_rule_state: Mapped[str | None] = mapped_column(String(32))
    attempted_action: Mapped[str | None] = mapped_column(String(32))

    record: Mapped[SignalReviewRecord] = relationship(back_populates="llm_reviews")
