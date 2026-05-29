from datetime import datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter
from pydantic import BaseModel

from app.backtest.engine import (
    BacktestBar,
    BacktestConfig,
    BacktestEngine,
    BacktestParameterSet,
    GridSearchReport,
    GridSearchResult,
    PerformanceSlice,
    SignalCandidate,
    SkippedSignal,
)


router = APIRouter(prefix="/backtests", tags=["backtests"])


class BacktestParameterRequest(BaseModel):
    name: str
    max_holding_bars: int


class BacktestSummaryRequest(BaseModel):
    start: datetime
    end: datetime
    parameter_sets: list[BacktestParameterRequest]


@router.post("/summary")
def run_backtest_summary(payload: BacktestSummaryRequest) -> dict[str, object]:
    grid_report = _sample_engine().run_grid_search(
        signals=_sample_signals(payload.start),
        bars=_sample_bars(payload.start),
        start=payload.start,
        end=payload.end,
        parameter_sets=[
            BacktestParameterSet(name=item.name, max_holding_bars=item.max_holding_bars)
            for item in payload.parameter_sets
        ],
        min_trades_for_robust=5,
        max_symbol_concentration=Decimal("0.60"),
    )
    return _grid_report_to_dict(payload, grid_report)


def _grid_report_to_dict(
    payload: BacktestSummaryRequest,
    grid_report: GridSearchReport,
) -> dict[str, object]:
    return {
        "start": payload.start.isoformat(),
        "end": payload.end.isoformat(),
        "best": _result_summary(grid_report.best) if grid_report.best else None,
        "results": [_result_summary(result) for result in grid_report.results],
        "reliability_note": grid_report.reliability_note,
    }


def _result_summary(result: GridSearchResult) -> dict[str, object]:
    report = result.report
    return {
        "name": result.name,
        "parameters": {"max_holding_bars": result.parameters.max_holding_bars},
        "total_trades": report.total_trades,
        "win_rate": str(report.win_rate),
        "mean_return": str(report.mean_return),
        "median_return": str(report.median_return),
        "max_drawdown": str(report.max_drawdown),
        "risk_flags": result.risk_flags,
        "symbol_concentration": {key: str(value) for key, value in result.symbol_concentration.items()},
        "by_signal_state": _slices_to_dict(report.by_signal_state),
        "by_wyckoff_bucket": _slices_to_dict(report.by_wyckoff_bucket),
        "skipped_signals": [_skipped_to_dict(item) for item in report.skipped_signals],
    }


def _slices_to_dict(items: dict[str, PerformanceSlice]) -> dict[str, dict[str, object]]:
    return {
        key: {
            "total_trades": value.total_trades,
            "win_rate": str(value.win_rate),
            "mean_return": str(value.mean_return),
            "median_return": str(value.median_return),
        }
        for key, value in items.items()
    }


def _skipped_to_dict(item: SkippedSignal) -> dict[str, object]:
    return {
        "ts_code": item.ts_code,
        "theme": item.theme,
        "signal_state": item.signal_state,
        "signal_time": item.signal_time.isoformat(),
        "reason": item.reason,
    }


def _sample_engine() -> BacktestEngine:
    return BacktestEngine(
        BacktestConfig(
            initial_cash=Decimal("100000"),
            position_pct=Decimal("0.30"),
            commission_rate=Decimal("0.0003"),
            stamp_tax_rate=Decimal("0.001"),
            slippage_rate=Decimal("0.001"),
            max_holding_bars=8,
            max_total_position_pct=Decimal("0.70"),
            max_theme_position_pct=Decimal("0.60"),
            max_symbol_position_pct=Decimal("0.40"),
        )
    )


def _sample_signals(base_time: datetime) -> list[SignalCandidate]:
    return [
        SignalCandidate(
            ts_code="600001.SH",
            state="confirmed_3buy",
            signal_time=base_time,
            wyckoff_score=86,
            structure_upper=Decimal("10.60"),
            structure_lower=Decimal("9.80"),
            target_price=Decimal("11.40"),
            theme="机器人",
        ),
        SignalCandidate(
            ts_code="600010.SH",
            state="proto_3buy",
            signal_time=base_time + timedelta(days=1),
            wyckoff_score=66,
            structure_upper=Decimal("10.60"),
            structure_lower=Decimal("9.80"),
            target_price=Decimal("11.40"),
            theme="CPO",
        ),
    ]


def _sample_bars(base_time: datetime) -> list[BacktestBar]:
    return [
        BacktestBar(
            ts_code="600001.SH",
            bar_time=base_time + timedelta(minutes=30),
            open=Decimal("10.90"),
            high=Decimal("10.95"),
            low=Decimal("10.80"),
            close=Decimal("10.88"),
            volume=1_000_000,
            amount=Decimal("108800000"),
        ),
        BacktestBar(
            ts_code="600001.SH",
            bar_time=base_time + timedelta(minutes=60),
            open=Decimal("10.88"),
            high=Decimal("11.50"),
            low=Decimal("10.82"),
            close=Decimal("11.42"),
            volume=1_200_000,
            amount=Decimal("137040000"),
        ),
        BacktestBar(
            ts_code="600010.SH",
            bar_time=base_time + timedelta(days=1, minutes=30),
            open=Decimal("10.70"),
            high=Decimal("10.82"),
            low=Decimal("10.30"),
            close=Decimal("10.36"),
            volume=900_000,
            amount=Decimal("93240000"),
        ),
        BacktestBar(
            ts_code="600010.SH",
            bar_time=base_time + timedelta(days=1, minutes=60),
            open=Decimal("10.34"),
            high=Decimal("10.40"),
            low=Decimal("9.76"),
            close=Decimal("9.82"),
            volume=1_400_000,
            amount=Decimal("137480000"),
        ),
    ]
