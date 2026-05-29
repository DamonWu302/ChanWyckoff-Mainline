from fastapi.testclient import TestClient

from app.main import create_app


def test_operations_split_endpoints_return_market_theme_core_and_signal_lists() -> None:
    client = TestClient(create_app())

    market_response = client.get("/api/market-regime?trade_date=2026-05-26")
    themes_response = client.get("/api/themes/mainlines?trade_date=2026-05-26")
    core_stocks_response = client.get("/api/themes/BK1234/core-stocks?trade_date=2026-05-26")
    signals_response = client.get("/api/signals?trade_date=2026-05-26")

    assert market_response.status_code == 200
    assert themes_response.status_code == 200
    assert core_stocks_response.status_code == 200
    assert signals_response.status_code == 200

    market = market_response.json()
    themes = themes_response.json()
    core_stocks = core_stocks_response.json()
    signals = signals_response.json()

    assert market["state"] == "neutral"
    assert market["recommended_exposure_pct"] == 45
    assert themes[0]["theme_code"] == "BK1234"
    assert themes[0]["label"] == "confirmed_mainline"
    assert themes[0]["core_stocks"][0]["rank"] == 1
    assert core_stocks[0]["ts_code"] == "600001.SH"
    assert signals[0]["state"] == "confirmed_3buy"
    assert signals[0]["suggested_action"] == "upgrade_position"
    assert signals[0]["evidence"]["structure"] == "30m_platform_upper_breakout"
