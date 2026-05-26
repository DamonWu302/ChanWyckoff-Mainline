from collections.abc import Iterator
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.review.signal_review import (
    LlmReviewPayload,
    ManualReviewPayload,
    SignalReviewService,
)


@pytest.fixture()
def db_session() -> Iterator[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    with SessionLocal() as session:
        yield session


def test_manual_review_status_history_and_performance_are_persisted(db_session: Session) -> None:
    service = SignalReviewService(db_session)
    signal_time = datetime(2026, 5, 26, 10, 30, tzinfo=timezone.utc)

    record = service.record_manual_review(
        ManualReviewPayload(
            signal_uid="600001.SH-20260526T103000-confirmed",
            ts_code="600001.SH",
            signal_time=signal_time,
            rule_state="confirmed_3buy",
            suggested_action="upgrade_position",
            manual_status="prepared",
            note="回踩缩量，等待计划价。",
            failure_reason=None,
            return_pct=None,
            max_drawdown_pct=None,
            holding_bars=None,
        )
    )
    updated = service.record_manual_review(
        ManualReviewPayload(
            signal_uid="600001.SH-20260526T103000-confirmed",
            ts_code="600001.SH",
            signal_time=signal_time,
            rule_state="confirmed_3buy",
            suggested_action="upgrade_position",
            manual_status="sold",
            note="按计划止盈。",
            failure_reason=None,
            return_pct=Decimal("0.0612"),
            max_drawdown_pct=Decimal("0.0180"),
            holding_bars=5,
        )
    )

    fetched = service.get_record("600001.SH-20260526T103000-confirmed")

    assert record.id == updated.id
    assert fetched is not None
    assert fetched.manual_status == "sold"
    assert fetched.rule_state == "confirmed_3buy"
    assert fetched.suggested_action == "upgrade_position"
    assert fetched.return_pct == Decimal("0.061200")
    assert fetched.max_drawdown_pct == Decimal("0.018000")
    assert fetched.holding_bars == 5
    assert [event.manual_status for event in fetched.events] == ["prepared", "sold"]
    assert fetched.events[-1].note == "按计划止盈。"


def test_llm_review_adds_explanation_without_changing_rule_result(db_session: Session) -> None:
    service = SignalReviewService(db_session)
    signal_uid = "600020.SH-20260526T140000-failed"
    service.record_manual_review(
        ManualReviewPayload(
            signal_uid=signal_uid,
            ts_code="600020.SH",
            signal_time=datetime(2026, 5, 26, 14, 0, tzinfo=timezone.utc),
            rule_state="failed_3buy",
            suggested_action="filter",
            manual_status="skipped",
            note="放量跌回中枢，不进入计划。",
            failure_reason="supply_returned",
            return_pct=None,
            max_drawdown_pct=None,
            holding_bars=None,
        )
    )

    review = service.attach_llm_review(
        LlmReviewPayload(
            signal_uid=signal_uid,
            provider="deepseek",
            model="deepseek-chat",
            background_summary="题材退潮时供应重新进入。",
            feature_summary="跌回平台内且量能放大。",
            forecast_summary="后续需要重新站回上沿再观察。",
            failure_type="heavy_volume_close_back_inside",
            attempted_rule_state="confirmed_3buy",
            attempted_action="upgrade_position",
        )
    )
    fetched = service.get_record(signal_uid)

    assert fetched is not None
    assert fetched.rule_state == "failed_3buy"
    assert fetched.suggested_action == "filter"
    assert fetched.llm_reviews[0].id == review.id
    assert fetched.llm_reviews[0].failure_type == "heavy_volume_close_back_inside"
    assert fetched.llm_reviews[0].attempted_rule_state == "confirmed_3buy"


def test_failure_distribution_counts_manual_and_llm_failure_types(db_session: Session) -> None:
    service = SignalReviewService(db_session)
    for index, failure_reason in enumerate(["supply_returned", "time_stop", "supply_returned"]):
        signal_uid = f"60000{index}.SH-20260526T140000-failed"
        service.record_manual_review(
            ManualReviewPayload(
                signal_uid=signal_uid,
                ts_code=f"60000{index}.SH",
                signal_time=datetime(2026, 5, 26, 14, index, tzinfo=timezone.utc),
                rule_state="failed_3buy",
                suggested_action="filter",
                manual_status="skipped",
                note="失败样本。",
                failure_reason=failure_reason,
                return_pct=None,
                max_drawdown_pct=None,
                holding_bars=None,
            )
        )
    service.attach_llm_review(
        LlmReviewPayload(
            signal_uid="600000.SH-20260526T140000-failed",
            provider="deepseek",
            model="deepseek-chat",
            background_summary="背景",
            feature_summary="特征",
            forecast_summary="预判",
            failure_type="heavy_volume_close_back_inside",
        )
    )

    distribution = service.failure_distribution()

    assert distribution.manual_failure_reasons == {
        "supply_returned": 2,
        "time_stop": 1,
    }
    assert distribution.llm_failure_types == {
        "heavy_volume_close_back_inside": 1,
    }
    assert distribution.total_failed_records == 3
