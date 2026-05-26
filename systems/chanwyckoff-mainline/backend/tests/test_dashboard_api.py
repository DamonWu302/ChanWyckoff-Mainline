from fastapi.testclient import TestClient

from app.main import create_app


def test_dashboard_endpoint_returns_operations_snapshot() -> None:
    client = TestClient(create_app())

    response = client.get("/api/dashboard")

    assert response.status_code == 200
    body = response.json()
    assert body["trade_date"] == "2026-05-26"
    assert body["market_regime"]["state"] == "neutral"
    assert body["market_regime"]["attack_allowed"] is True
    assert body["market_regime"]["suppress_new_signals"] is False
    assert body["market_regime"]["recommended_exposure_pct"] == 45
    assert body["mainlines"][0]["label"] == "confirmed_mainline"
    assert body["mainlines"][0]["core_stocks"][0]["rank"] == 1
    assert body["signals"][0]["state"] == "confirmed_3buy"
    assert body["signals"][0]["suggested_action"] == "upgrade_position"
    assert body["signals"][0]["evidence"]["wyckoff_forecast"] == "continuation_expected"
    assert body["filters"]["states"] == ["proto_3buy", "confirmed_3buy", "failed_3buy"]
