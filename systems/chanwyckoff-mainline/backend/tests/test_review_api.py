from collections.abc import Iterator
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import create_app


@pytest.fixture()
def db_session() -> Iterator[Session]:
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    with SessionLocal() as session:
        yield session


@pytest.fixture()
def client(db_session: Session) -> Iterator[TestClient]:
    app = create_app()

    def override_db() -> Iterator[Session]:
        yield db_session

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_review_api_records_manual_status_and_llm_summary(client: TestClient) -> None:
    signal_uid = "600001.SH-20260526T103000-confirmed"

    manual_response = client.post(
        "/api/reviews/manual",
        json={
            "signal_uid": signal_uid,
            "ts_code": "600001.SH",
            "signal_time": datetime(2026, 5, 26, 10, 30, tzinfo=timezone.utc).isoformat(),
            "rule_state": "confirmed_3buy",
            "suggested_action": "upgrade_position",
            "manual_status": "prepared",
            "note": "等待计划价。",
            "failure_reason": None,
            "return_pct": None,
            "max_drawdown_pct": None,
            "holding_bars": None,
        },
    )
    llm_response = client.post(
        f"/api/reviews/{signal_uid}/llm",
        json={
            "provider": "deepseek",
            "model": "deepseek-chat",
            "background_summary": "主线仍强。",
            "feature_summary": "缩量回踩。",
            "forecast_summary": "继续观察承接。",
            "failure_type": None,
            "attempted_rule_state": "failed_3buy",
            "attempted_action": "filter",
        },
    )
    detail_response = client.get(f"/api/reviews/{signal_uid}")

    assert manual_response.status_code == 200
    assert llm_response.status_code == 200
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["signal_uid"] == signal_uid
    assert detail["rule_state"] == "confirmed_3buy"
    assert detail["suggested_action"] == "upgrade_position"
    assert detail["manual_status"] == "prepared"
    assert detail["events"][0]["note"] == "等待计划价。"
    assert detail["llm_reviews"][0]["attempted_rule_state"] == "failed_3buy"


def test_review_api_accepts_signal_performance(client: TestClient) -> None:
    response = client.post(
        "/api/reviews/manual",
        json={
            "signal_uid": "600002.SH-20260526T140000-sold",
            "ts_code": "600002.SH",
            "signal_time": datetime(2026, 5, 26, 14, 0, tzinfo=timezone.utc).isoformat(),
            "rule_state": "proto_3buy",
            "suggested_action": "light_position",
            "manual_status": "sold",
            "note": "时间止损离场。",
            "failure_reason": "time_stop",
            "return_pct": str(Decimal("-0.0215")),
            "max_drawdown_pct": str(Decimal("0.0340")),
            "holding_bars": 8,
        },
    )

    body = response.json()

    assert response.status_code == 200
    assert body["return_pct"] == " -0.021500".strip()
    assert body["max_drawdown_pct"] == "0.034000"
    assert body["holding_bars"] == 8


def test_review_stats_endpoint_returns_failure_distribution(client: TestClient) -> None:
    for index, failure_reason in enumerate(["supply_returned", "time_stop", "supply_returned"]):
        client.post(
            "/api/reviews/manual",
            json={
                "signal_uid": f"60010{index}.SH-20260526T140000-failed",
                "ts_code": f"60010{index}.SH",
                "signal_time": datetime(2026, 5, 26, 14, index, tzinfo=timezone.utc).isoformat(),
                "rule_state": "failed_3buy",
                "suggested_action": "filter",
                "manual_status": "skipped",
                "note": "失败样本。",
                "failure_reason": failure_reason,
                "return_pct": None,
                "max_drawdown_pct": None,
                "holding_bars": None,
            },
        )

    response = client.get("/api/reviews/stats/failures")

    assert response.status_code == 200
    assert response.json() == {
        "manual_failure_reasons": {
            "supply_returned": 2,
            "time_stop": 1,
        },
        "llm_failure_types": {},
        "total_failed_records": 3,
    }
