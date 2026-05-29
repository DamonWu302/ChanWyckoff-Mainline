from fastapi.testclient import TestClient

from app.main import create_app


def test_backtest_summary_endpoint_runs_date_range_and_parameter_grid() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/backtests/summary",
        json={
            "start": "2026-05-25T10:00:00+00:00",
            "end": "2026-05-27T10:00:00+00:00",
            "parameter_sets": [
                {"name": "fast", "max_holding_bars": 1},
                {"name": "patient", "max_holding_bars": 8},
            ],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["start"] == "2026-05-25T10:00:00+00:00"
    assert body["end"] == "2026-05-27T10:00:00+00:00"
    assert body["best"]["name"] == "fast"
    assert body["results"][0]["name"] == "fast"
    assert body["results"][0]["total_trades"] == 2
    assert body["results"][0]["by_signal_state"]["confirmed_3buy"]["total_trades"] == 1
    assert body["results"][0]["by_wyckoff_bucket"]["80-100"]["total_trades"] == 1
    assert "small_sample" in body["results"][0]["risk_flags"]
    assert body["reliability_note"] == "theme_history_reliability_requires_point_in_time_constituents"
