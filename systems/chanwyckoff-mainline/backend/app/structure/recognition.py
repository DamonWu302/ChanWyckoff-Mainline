from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Literal


StructureLabel = Literal["statistical_platform", "converging_platform", "chan_center"]
FractalKind = Literal["top", "bottom"]


@dataclass(frozen=True, slots=True)
class Bar30m:
    bar_time: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    amount: Decimal


@dataclass(frozen=True, slots=True)
class RecognizedStructure:
    label: StructureLabel
    start_time: datetime
    end_time: datetime
    upper: Decimal
    lower: Decimal
    mid: Decimal
    duration_bars: int
    amplitude: Decimal
    overlap_rate: Decimal
    upper_tests: int
    quality_score: int


@dataclass(frozen=True, slots=True)
class Fractal:
    kind: FractalKind
    bar_time: datetime
    price: Decimal


@dataclass(frozen=True, slots=True)
class Stroke:
    start: Fractal
    end: Fractal
    direction: Literal["up", "down"]


@dataclass(frozen=True, slots=True)
class StructureRecognitionResult:
    structures: list[RecognizedStructure] = field(default_factory=list)
    fractals: list[Fractal] = field(default_factory=list)
    strokes: list[Stroke] = field(default_factory=list)


class StructureRecognitionService:
    def __init__(
        self,
        min_window: int = 10,
        max_amplitude_ratio: Decimal = Decimal("0.12"),
        min_overlap_rate: Decimal = Decimal("0.65"),
    ) -> None:
        self.min_window = min_window
        self.max_amplitude_ratio = max_amplitude_ratio
        self.min_overlap_rate = min_overlap_rate

    def analyze(self, bars: list[Bar30m]) -> StructureRecognitionResult:
        fractals = self._fractals(bars)
        strokes = self._strokes(fractals)
        if len(bars) < self.min_window:
            return StructureRecognitionResult(fractals=fractals, strokes=strokes)

        window = bars[-self.min_window :]
        if self._is_one_way_downtrend(window):
            return StructureRecognitionResult(fractals=fractals, strokes=strokes)

        upper = max(bar.high for bar in window)
        lower = min(bar.low for bar in window)
        mid = (upper + lower) / Decimal("2")
        amplitude = upper - lower
        if mid <= 0:
            return StructureRecognitionResult(fractals=fractals, strokes=strokes)
        amplitude_ratio = amplitude / mid

        overlap_rate = self._overlap_rate(window)
        if overlap_rate < self.min_overlap_rate:
            return StructureRecognitionResult(fractals=fractals, strokes=strokes)

        is_converging = self._is_converging(window)
        if amplitude_ratio > self.max_amplitude_ratio and not is_converging:
            return StructureRecognitionResult(fractals=fractals, strokes=strokes)

        chan_center = None if is_converging else self._chan_center(strokes, bars, amplitude)
        if chan_center is not None:
            return StructureRecognitionResult(
                structures=[chan_center],
                fractals=fractals,
                strokes=strokes,
            )

        upper_tests = self._upper_tests(window, upper, amplitude)
        quality_score = self._quality_score(
            amplitude_ratio, overlap_rate, upper_tests, len(window), is_converging
        )
        return StructureRecognitionResult(
            structures=[
                RecognizedStructure(
                    label="converging_platform" if is_converging else "statistical_platform",
                    start_time=window[0].bar_time,
                    end_time=window[-1].bar_time,
                    upper=upper,
                    lower=lower,
                    mid=mid,
                    duration_bars=len(window),
                    amplitude=amplitude,
                    overlap_rate=overlap_rate,
                    upper_tests=upper_tests,
                    quality_score=quality_score,
                )
            ],
            fractals=fractals,
            strokes=strokes,
        )

    def _is_one_way_downtrend(self, bars: list[Bar30m]) -> bool:
        lower_close_count = 0
        lower_high_count = 0
        for previous, current in zip(bars, bars[1:]):
            if current.close < previous.close:
                lower_close_count += 1
            if current.high < previous.high:
                lower_high_count += 1
        threshold = max(5, int((len(bars) - 1) * 0.75))
        return lower_close_count >= threshold and lower_high_count >= threshold

    def _chan_center(
        self,
        strokes: list[Stroke],
        bars: list[Bar30m],
        window_amplitude: Decimal,
    ) -> RecognizedStructure | None:
        if len(strokes) < 3:
            return None
        for stroke_group in reversed([strokes[index : index + 3] for index in range(len(strokes) - 2)]):
            upper = min(self._stroke_high(stroke) for stroke in stroke_group)
            lower = max(self._stroke_low(stroke) for stroke in stroke_group)
            if upper <= lower:
                continue
            mid = (upper + lower) / Decimal("2")
            amplitude = upper - lower
            if mid <= 0 or amplitude / mid > self.max_amplitude_ratio:
                continue
            if amplitude > window_amplitude * Decimal("0.60"):
                continue

            start_time = stroke_group[0].start.bar_time
            end_time = stroke_group[-1].end.bar_time
            window = [bar for bar in bars if start_time <= bar.bar_time <= end_time]
            if len(window) < 4:
                continue

            overlap_rate = self._overlap_rate(window)
            upper_tests = self._upper_tests(window, upper, amplitude)
            quality_score = self._quality_score(
                amplitude / mid,
                max(overlap_rate, self.min_overlap_rate),
                max(upper_tests, 2),
                len(window),
                False,
            )
            return RecognizedStructure(
                label="chan_center",
                start_time=start_time,
                end_time=end_time,
                upper=upper,
                lower=lower,
                mid=mid,
                duration_bars=len(window),
                amplitude=amplitude,
                overlap_rate=overlap_rate,
                upper_tests=upper_tests,
                quality_score=max(70, quality_score + 8),
            )
        return None

    def _stroke_high(self, stroke: Stroke) -> Decimal:
        return max(stroke.start.price, stroke.end.price)

    def _stroke_low(self, stroke: Stroke) -> Decimal:
        return min(stroke.start.price, stroke.end.price)

    def _overlap_rate(self, bars: list[Bar30m]) -> Decimal:
        pair_count = 0
        overlap_count = 0
        for previous, current in zip(bars, bars[1:]):
            pair_count += 1
            overlap_low = max(previous.low, current.low)
            overlap_high = min(previous.high, current.high)
            if overlap_high > overlap_low:
                overlap_count += 1
        if pair_count == 0:
            return Decimal("0")
        return Decimal(overlap_count) / Decimal(pair_count)

    def _upper_tests(self, bars: list[Bar30m], upper: Decimal, amplitude: Decimal) -> int:
        tolerance = max(amplitude * Decimal("0.12"), Decimal("0.01"))
        return sum(1 for bar in bars if upper - bar.high <= tolerance)

    def _is_converging(self, bars: list[Bar30m]) -> bool:
        if len(bars) < 8:
            return False
        half = len(bars) // 2
        first = bars[:half]
        second = bars[half:]
        first_range = max(bar.high for bar in first) - min(bar.low for bar in first)
        second_range = max(bar.high for bar in second) - min(bar.low for bar in second)
        lower_highs = sum(1 for previous, current in zip(bars, bars[1:]) if current.high <= previous.high)
        higher_lows = sum(1 for previous, current in zip(bars, bars[1:]) if current.low >= previous.low)
        return (
            second_range <= first_range * Decimal("0.70")
            and lower_highs >= int((len(bars) - 1) * 0.65)
            and higher_lows >= int((len(bars) - 1) * 0.65)
        )

    def _quality_score(
        self,
        amplitude_ratio: Decimal,
        overlap_rate: Decimal,
        upper_tests: int,
        duration_bars: int,
        is_converging: bool,
    ) -> int:
        compact_score = max(
            Decimal("0"),
            Decimal("1") - (amplitude_ratio / (self.max_amplitude_ratio * Decimal("1.8"))),
        )
        test_score = min(Decimal(upper_tests) / Decimal("4"), Decimal("1"))
        duration_score = min(Decimal(duration_bars) / Decimal("16"), Decimal("1"))
        convergence_bonus = Decimal("12") if is_converging else Decimal("0")
        score = (
            compact_score * Decimal("35")
            + overlap_rate * Decimal("35")
            + test_score * Decimal("20")
            + duration_score * Decimal("10")
            + convergence_bonus
        )
        return max(0, min(100, int(score)))

    def _fractals(self, bars: list[Bar30m]) -> list[Fractal]:
        fractals: list[Fractal] = []
        for previous, current, following in zip(bars, bars[1:], bars[2:]):
            if current.high > previous.high and current.high >= following.high:
                fractals.append(Fractal(kind="top", bar_time=current.bar_time, price=current.high))
            if current.low < previous.low and current.low <= following.low:
                fractals.append(Fractal(kind="bottom", bar_time=current.bar_time, price=current.low))
            if current.close > previous.close and current.close >= following.close:
                fractals.append(Fractal(kind="top", bar_time=current.bar_time, price=current.high))
            if current.close < previous.close and current.close <= following.close:
                fractals.append(Fractal(kind="bottom", bar_time=current.bar_time, price=current.low))
        return self._dedupe_fractals(fractals)

    def _dedupe_fractals(self, fractals: list[Fractal]) -> list[Fractal]:
        deduped: list[Fractal] = []
        for fractal in fractals:
            if deduped and deduped[-1].bar_time == fractal.bar_time and deduped[-1].kind == fractal.kind:
                continue
            deduped.append(fractal)
        return deduped

    def _strokes(self, fractals: list[Fractal]) -> list[Stroke]:
        strokes: list[Stroke] = []
        last: Fractal | None = None
        for fractal in fractals:
            if last is None:
                last = fractal
                continue
            if fractal.kind == last.kind:
                if fractal.kind == "top" and fractal.price > last.price:
                    last = fractal
                elif fractal.kind == "bottom" and fractal.price < last.price:
                    last = fractal
                continue
            direction = "up" if last.kind == "bottom" and fractal.kind == "top" else "down"
            strokes.append(Stroke(start=last, end=fractal, direction=direction))
            last = fractal
        return strokes
