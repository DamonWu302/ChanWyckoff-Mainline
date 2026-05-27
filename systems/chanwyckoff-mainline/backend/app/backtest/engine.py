from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Callable, Literal


SignalState = Literal["proto_3buy", "confirmed_3buy", "failed_3buy"]
ExitReason = Literal["target_reached", "stop_loss", "time_stop", "end_of_data"]

RETURN_PLACES = Decimal("0.000001")
PRICE_PLACES = Decimal("0.0001")


@dataclass(frozen=True, slots=True)
class SignalCandidate:
    ts_code: str
    state: SignalState
    signal_time: datetime
    wyckoff_score: int
    structure_upper: Decimal
    structure_lower: Decimal
    target_price: Decimal
    theme: str | None = None


@dataclass(frozen=True, slots=True)
class BacktestBar:
    ts_code: str
    bar_time: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    amount: Decimal
    is_suspended: bool = False
    limit_up: bool = False
    limit_down: bool = False


@dataclass(frozen=True, slots=True)
class BacktestConfig:
    initial_cash: Decimal
    position_pct: Decimal
    commission_rate: Decimal
    stamp_tax_rate: Decimal
    slippage_rate: Decimal
    max_holding_bars: int
    max_total_position_pct: Decimal | None = None
    max_theme_position_pct: Decimal | None = None
    max_symbol_position_pct: Decimal | None = None


@dataclass(frozen=True, slots=True)
class BacktestParameterSet:
    name: str
    max_holding_bars: int


@dataclass(frozen=True, slots=True)
class BacktestTrade:
    ts_code: str
    theme: str | None
    signal_state: SignalState
    wyckoff_score: int
    entry_time: datetime
    exit_time: datetime
    entry_price: Decimal
    exit_price: Decimal
    exit_reason: ExitReason
    holding_bars: int
    net_return: Decimal


@dataclass(frozen=True, slots=True)
class SkippedSignal:
    ts_code: str
    theme: str | None
    signal_state: SignalState
    signal_time: datetime
    reason: str


@dataclass(frozen=True, slots=True)
class PerformanceSlice:
    total_trades: int
    win_rate: Decimal
    mean_return: Decimal
    median_return: Decimal


@dataclass(frozen=True, slots=True)
class BacktestReport:
    trades: list[BacktestTrade]
    skipped_signals: list[SkippedSignal]
    total_trades: int
    win_rate: Decimal
    mean_return: Decimal
    median_return: Decimal
    max_drawdown: Decimal
    by_signal_state: dict[str, PerformanceSlice] = field(default_factory=dict)
    by_wyckoff_bucket: dict[str, PerformanceSlice] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class GridSearchResult:
    name: str
    parameters: BacktestParameterSet
    report: BacktestReport
    risk_flags: list[str]
    symbol_concentration: dict[str, Decimal]


@dataclass(frozen=True, slots=True)
class GridSearchReport:
    results: list[GridSearchResult]
    best: GridSearchResult | None
    reliability_note: str


class BacktestEngine:
    def __init__(self, config: BacktestConfig) -> None:
        self.config = config

    def run(
        self,
        signals: list[SignalCandidate],
        bars: list[BacktestBar],
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> BacktestReport:
        signals = self._signals_in_range(signals, start, end)
        bars_by_symbol = self._bars_by_symbol(bars)
        candidates = [
            (signal, trade)
            for signal in sorted(signals, key=lambda item: item.signal_time)
            if signal.state != "failed_3buy"
            for trade in [self._simulate_signal(signal, bars_by_symbol.get(signal.ts_code, []))]
            if trade is not None
        ]
        trades, skipped_signals = self._apply_capacity_limits(candidates)
        return self._build_report(trades, skipped_signals)

    def run_grid_search(
        self,
        signals: list[SignalCandidate],
        bars: list[BacktestBar],
        parameter_sets: list[BacktestParameterSet],
        start: datetime | None = None,
        end: datetime | None = None,
        min_trades_for_robust: int = 30,
        max_symbol_concentration: Decimal = Decimal("0.35"),
    ) -> GridSearchReport:
        results = [
            self._run_parameter_set(
                parameter_set,
                signals,
                bars,
                start,
                end,
                min_trades_for_robust,
                max_symbol_concentration,
            )
            for parameter_set in parameter_sets
        ]
        results = sorted(results, key=lambda item: item.report.mean_return, reverse=True)
        return GridSearchReport(
            results=results,
            best=results[0] if results else None,
            reliability_note="theme_history_reliability_requires_point_in_time_constituents",
        )

    def _simulate_signal(
        self,
        signal: SignalCandidate,
        bars: list[BacktestBar],
    ) -> BacktestTrade | None:
        future_bars = [bar for bar in bars if bar.bar_time > signal.signal_time]
        entry_bar = self._first_buyable_bar(future_bars)
        if entry_bar is None:
            return None

        entry_index = future_bars.index(entry_bar)
        entry_price = self._buy_price(entry_bar.open)
        exit_bar = entry_bar
        exit_price = self._sell_price(entry_bar.close)
        exit_reason: ExitReason = "end_of_data"
        holding_bars = 0

        for offset, bar in enumerate(future_bars[entry_index + 1 :], start=1):
            if bar.is_suspended:
                continue
            holding_bars = offset
            if bar.low <= signal.structure_lower and not bar.limit_down:
                exit_bar = bar
                exit_price = self._sell_price(signal.structure_lower)
                exit_reason = "stop_loss"
                break
            if bar.high >= signal.target_price and not bar.limit_down:
                exit_bar = bar
                exit_price = self._sell_price(signal.target_price)
                exit_reason = "target_reached"
                break
            if offset >= self.config.max_holding_bars and not bar.limit_down:
                exit_bar = bar
                exit_price = self._sell_price(bar.close)
                exit_reason = "time_stop"
                break
            exit_bar = bar
            exit_price = self._sell_price(bar.close)

        return BacktestTrade(
            ts_code=signal.ts_code,
            theme=signal.theme,
            signal_state=signal.state,
            wyckoff_score=signal.wyckoff_score,
            entry_time=entry_bar.bar_time,
            exit_time=exit_bar.bar_time,
            entry_price=entry_price,
            exit_price=exit_price,
            exit_reason=exit_reason,
            holding_bars=holding_bars,
            net_return=self._net_return(entry_price, exit_price),
        )

    def _build_report(
        self,
        trades: list[BacktestTrade],
        skipped_signals: list[SkippedSignal] | None = None,
    ) -> BacktestReport:
        skipped_signals = skipped_signals or []
        returns = [trade.net_return for trade in trades]
        return BacktestReport(
            trades=trades,
            skipped_signals=skipped_signals,
            total_trades=len(trades),
            win_rate=self._win_rate(returns),
            mean_return=self._mean(returns),
            median_return=self._median(returns),
            max_drawdown=self._max_drawdown(returns),
            by_signal_state=self._group_by(trades, lambda trade: trade.signal_state),
            by_wyckoff_bucket=self._group_by(
                trades,
                lambda trade: self._wyckoff_bucket(trade.wyckoff_score),
            ),
        )

    def _run_parameter_set(
        self,
        parameter_set: BacktestParameterSet,
        signals: list[SignalCandidate],
        bars: list[BacktestBar],
        start: datetime | None,
        end: datetime | None,
        min_trades_for_robust: int,
        max_symbol_concentration: Decimal,
    ) -> GridSearchResult:
        engine = BacktestEngine(
            BacktestConfig(
                initial_cash=self.config.initial_cash,
                position_pct=self.config.position_pct,
                commission_rate=self.config.commission_rate,
                stamp_tax_rate=self.config.stamp_tax_rate,
                slippage_rate=self.config.slippage_rate,
                max_holding_bars=parameter_set.max_holding_bars,
                max_total_position_pct=self.config.max_total_position_pct,
                max_theme_position_pct=self.config.max_theme_position_pct,
                max_symbol_position_pct=self.config.max_symbol_position_pct,
            )
        )
        report = engine.run(signals=signals, bars=bars, start=start, end=end)
        symbol_concentration = self._symbol_concentration(report.trades)
        risk_flags = self._risk_flags(
            report,
            symbol_concentration,
            min_trades_for_robust,
            max_symbol_concentration,
        )
        return GridSearchResult(
            name=parameter_set.name,
            parameters=parameter_set,
            report=report,
            risk_flags=risk_flags,
            symbol_concentration=symbol_concentration,
        )

    def _signals_in_range(
        self,
        signals: list[SignalCandidate],
        start: datetime | None,
        end: datetime | None,
    ) -> list[SignalCandidate]:
        return [
            signal
            for signal in signals
            if (start is None or signal.signal_time >= start)
            and (end is None or signal.signal_time <= end)
        ]

    def _apply_capacity_limits(
        self,
        candidates: list[tuple[SignalCandidate, BacktestTrade]],
    ) -> tuple[list[BacktestTrade], list[SkippedSignal]]:
        accepted: list[BacktestTrade] = []
        skipped: list[SkippedSignal] = []
        for signal, trade in sorted(candidates, key=lambda item: item[1].entry_time):
            active_trades = [
                accepted_trade
                for accepted_trade in accepted
                if accepted_trade.exit_time > trade.entry_time
            ]
            reason = self._capacity_reject_reason(signal, active_trades)
            if reason is not None:
                skipped.append(
                    SkippedSignal(
                        ts_code=signal.ts_code,
                        theme=signal.theme,
                        signal_state=signal.state,
                        signal_time=signal.signal_time,
                        reason=reason,
                    )
                )
                continue
            accepted.append(trade)
        return accepted, skipped

    def _capacity_reject_reason(
        self,
        signal: SignalCandidate,
        active_trades: list[BacktestTrade],
    ) -> str | None:
        next_position = self.config.position_pct
        if self.config.max_symbol_position_pct is not None:
            symbol_exposure = next_position + sum(
                self.config.position_pct for trade in active_trades if trade.ts_code == signal.ts_code
            )
            if symbol_exposure > self.config.max_symbol_position_pct:
                return "symbol_capacity_exceeded"

        if self.config.max_theme_position_pct is not None and signal.theme is not None:
            theme_exposure = next_position + sum(
                self.config.position_pct for trade in active_trades if trade.theme == signal.theme
            )
            if theme_exposure > self.config.max_theme_position_pct:
                return "theme_capacity_exceeded"

        if self.config.max_total_position_pct is not None:
            total_exposure = next_position + (self.config.position_pct * Decimal(len(active_trades)))
            if total_exposure > self.config.max_total_position_pct:
                return "total_capacity_exceeded"
        return None

    def _group_by(
        self,
        trades: list[BacktestTrade],
        key_for: Callable[[BacktestTrade], str],
    ) -> dict[str, PerformanceSlice]:
        grouped: dict[str, list[Decimal]] = defaultdict(list)
        for trade in trades:
            grouped[key_for(trade)].append(trade.net_return)
        return {
            key: PerformanceSlice(
                total_trades=len(values),
                win_rate=self._win_rate(values),
                mean_return=self._mean(values),
                median_return=self._median(values),
            )
            for key, values in grouped.items()
        }

    def _first_buyable_bar(self, bars: list[BacktestBar]) -> BacktestBar | None:
        return next(
            (bar for bar in bars if not bar.is_suspended and not bar.limit_up and bar.volume > 0),
            None,
        )

    def _buy_price(self, price: Decimal) -> Decimal:
        return self._money(price * (Decimal("1") + self.config.slippage_rate))

    def _sell_price(self, price: Decimal) -> Decimal:
        return self._money(price * (Decimal("1") - self.config.slippage_rate))

    def _net_return(self, entry_price: Decimal, exit_price: Decimal) -> Decimal:
        buy_cost = entry_price * (Decimal("1") + self.config.commission_rate)
        sell_proceeds = exit_price * (
            Decimal("1") - self.config.commission_rate - self.config.stamp_tax_rate
        )
        return self._return((sell_proceeds - buy_cost) / buy_cost)

    def _max_drawdown(self, returns: list[Decimal]) -> Decimal:
        equity = self.config.initial_cash
        peak = equity
        max_drawdown = Decimal("0")
        for item_return in returns:
            equity *= Decimal("1") + (item_return * self.config.position_pct)
            peak = max(peak, equity)
            if peak > 0:
                max_drawdown = max(max_drawdown, (peak - equity) / peak)
        return self._return(max_drawdown)

    def _win_rate(self, returns: list[Decimal]) -> Decimal:
        if not returns:
            return Decimal("0")
        return self._return(Decimal(sum(1 for item in returns if item > 0)) / Decimal(len(returns)))

    def _mean(self, returns: list[Decimal]) -> Decimal:
        if not returns:
            return Decimal("0")
        return self._return(sum(returns, Decimal("0")) / Decimal(len(returns)))

    def _median(self, returns: list[Decimal]) -> Decimal:
        if not returns:
            return Decimal("0")
        ordered = sorted(returns)
        midpoint = len(ordered) // 2
        if len(ordered) % 2 == 1:
            return ordered[midpoint]
        return self._return((ordered[midpoint - 1] + ordered[midpoint]) / Decimal("2"))

    def _money(self, value: Decimal) -> Decimal:
        return value.quantize(PRICE_PLACES, rounding=ROUND_HALF_UP)

    def _return(self, value: Decimal) -> Decimal:
        return value.quantize(RETURN_PLACES, rounding=ROUND_HALF_UP).normalize()

    def _wyckoff_bucket(self, score: int) -> str:
        if score >= 80:
            return "80-100"
        if score >= 60:
            return "60-79"
        if score >= 40:
            return "40-59"
        return "0-39"

    def _symbol_concentration(self, trades: list[BacktestTrade]) -> dict[str, Decimal]:
        if not trades:
            return {}
        total = Decimal(len(trades))
        symbols = sorted({trade.ts_code for trade in trades})
        return {
            symbol: self._return(
                Decimal(sum(1 for trade in trades if trade.ts_code == symbol)) / total
            )
            for symbol in symbols
        }

    def _risk_flags(
        self,
        report: BacktestReport,
        symbol_concentration: dict[str, Decimal],
        min_trades_for_robust: int,
        max_symbol_concentration: Decimal,
    ) -> list[str]:
        flags = []
        if report.total_trades < min_trades_for_robust:
            flags.append("small_sample")
        if any(value > max_symbol_concentration for value in symbol_concentration.values()):
            flags.append("symbol_concentration")
        return flags

    def _bars_by_symbol(self, bars: list[BacktestBar]) -> dict[str, list[BacktestBar]]:
        grouped: dict[str, list[BacktestBar]] = defaultdict(list)
        for bar in bars:
            grouped[bar.ts_code].append(bar)
        return {
            ts_code: sorted(symbol_bars, key=lambda item: item.bar_time)
            for ts_code, symbol_bars in grouped.items()
        }
