from fastapi.testclient import TestClient

from app.main import create_app


def test_signal_detail_endpoint_returns_structure_price_and_risk_evidence() -> None:
    client = TestClient(create_app())

    response = client.get("/api/signals/600001.SH/detail")

    assert response.status_code == 200
    body = response.json()
    assert body["ts_code"] == "600001.SH"
    assert body["state"] == "confirmed_3buy"
    assert body["suggested_action"] == "upgrade_position"
    assert body["structure"]["label"] == "statistical_platform"
    assert body["structure"]["upper"] == "10.6000"
    assert body["structure"]["lower"] == "9.8000"
    assert body["price_volume"]["breakout_volume_ratio"] == "1.85"
    assert body["wyckoff"]["forecast"] == "continuation_expected"
    assert body["risk"]["position_pct"] == 25
    assert body["risk"]["stop_loss"] == "9.8000"
    assert body["risk"]["invalidations"] == [
        "close_back_inside_structure",
        "heavy_volume_supply_return",
        "pullback_timeout",
    ]


def test_signal_detail_endpoint_returns_404_for_unknown_symbol() -> None:
    client = TestClient(create_app())

    response = client.get("/api/signals/000000.SH/detail")

    assert response.status_code == 404
