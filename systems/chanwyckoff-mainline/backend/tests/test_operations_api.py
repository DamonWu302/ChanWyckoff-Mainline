from fastapi.testclient import TestClient

from app.main import create_app


def test_operations_split_endpoints_return_market_theme_core_and_signal_lists() -> None:
    client = TestClient(create_app())

    market_response = client.get("/api/market-regime")
    themes_response = client.get("/api/themes/mainlines")
    signals_response = client.get("/api/signals")

    assert market_response.status_code == 200
    assert themes_response.status_code == 200
    assert signals_response.status_code == 200

    market = market_response.json()
    themes = themes_response.json()
    signals = signals_response.json()

    assert market["state"] == "neutral"
    assert market["recommended_exposure_pct"] == 45
    assert themes[0]["label"] == "confirmed_mainline"
    assert themes[0]["core_stocks"][0]["rank"] == 1
    assert signals[0]["state"] == "confirmed_3buy"
    assert signals[0]["suggested_action"] == "upgrade_position"
    assert signals[0]["evidence"]["structure"] == "30m_platform_upper_breakout"
