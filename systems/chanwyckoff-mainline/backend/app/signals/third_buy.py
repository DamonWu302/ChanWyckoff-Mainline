from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Literal


ThirdBuyState = Literal["proto_3buy", "confirmed_3buy", "failed_3buy"]
SignalAction = Literal["light_position", "upgrade_position", "observe", "filter"]


@dataclass(frozen=True, slots=True)
class ThirdBuyStructure:
    ts_code: str
    upper: Decimal
    lower: Decimal
    mid: Decimal
    quality_score: int
    platform_avg_volume: int


@dataclass(frozen=True, slots=True)
class BreakoutBar:
    bar_time: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    amount: Decimal


@dataclass(frozen=True, slots=True)
class PullbackBar:
    bar_time: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    amount: Decimal
    atr: Decimal


@dataclass(frozen=True, slots=True)
class WyckoffAssessment:
    background: str
    features: dict[str, str]
    forecast: str
    score: int


@dataclass(frozen=True, slots=True)
class ThirdBuySignal:
    ts_code: str
    state: ThirdBuyState
    action: SignalAction
    signal_time: datetime
    structure_score: int
    breakout_strength: Decimal
    volume_ratio: Decimal
    wyckoff: WyckoffAssessment


class ThirdBuySignalService:
    def __init__(
        self,
        min_structure_score: int = 70,
        min_close_breakout_pct: Decimal = Decimal("0.005"),
        min_volume_ratio: Decimal = Decimal("1.50"),
    ) -> None:
        self.min_structure_score = min_structure_score
        self.min_close_breakout_pct = min_close_breakout_pct
        self.min_volume_ratio = min_volume_ratio

    def evaluate_breakout(
        self,
        structure: ThirdBuyStructure,
        breakout: BreakoutBar,
    ) -> ThirdBuySignal | None:
        if structure.quality_score < self.min_structure_score:
            return None
        if structure.upper <= 0 or structure.platform_avg_volume <= 0:
            return None

        breakout_strength = (breakout.close - structure.upper) / structure.upper
        if breakout_strength < self.min_close_breakout_pct:
            return None

        volume_ratio = Decimal(breakout.volume) / Decimal(structure.platform_avg_volume)
        if volume_ratio < self.min_volume_ratio:
            return None

        wyckoff = self._wyckoff_for_breakout(structure, breakout_strength, volume_ratio)
        return ThirdBuySignal(
            ts_code=structure.ts_code,
            state="proto_3buy",
            action="light_position",
            signal_time=breakout.bar_time,
            structure_score=structure.quality_score,
            breakout_strength=breakout_strength,
            volume_ratio=volume_ratio,
            wyckoff=wyckoff,
        )

    def evaluate_pullback(
        self,
        structure: ThirdBuyStructure,
        breakout: BreakoutBar,
        pullbacks: list[PullbackBar],
    ) -> ThirdBuySignal | None:
        if not pullbacks:
            return None
        if self.evaluate_breakout(structure, breakout) is None:
            return None
        if len(pullbacks) > 8:
            return self._failed_signal(
                structure,
                breakout,
                pullbacks[-1].bar_time,
                "pullback_timeout",
                "confirmation_expired",
            )

        heavy_volume_breakdown = any(
            bar.close < structure.upper and bar.volume >= structure.platform_avg_volume
            for bar in pullbacks
        )
        if heavy_volume_breakdown:
            return self._failed_signal(
                structure,
                breakout,
                pullbacks[-1].bar_time,
                "heavy_volume_close_back_inside",
                "supply_returned",
            )

        effective_breakdown = any(bar.close < structure.upper for bar in pullbacks)
        if effective_breakdown:
            return self._failed_signal(
                structure,
                breakout,
                pullbacks[-1].bar_time,
                "close_back_inside",
                "breakout_needs_repair",
            )

        touched_support = any(self._touches_upper_support(structure, bar) for bar in pullbacks)
        if not touched_support:
            return None

        max_pullback_volume = max(bar.volume for bar in pullbacks)
        volume_is_shrinking = (
            max_pullback_volume < breakout.volume
            and max_pullback_volume < structure.platform_avg_volume
        )
        if not volume_is_shrinking:
            return None

        wyckoff = self._wyckoff_for_confirmed_pullback(structure, breakout, pullbacks)
        return ThirdBuySignal(
            ts_code=structure.ts_code,
            state="confirmed_3buy",
            action="upgrade_position",
            signal_time=pullbacks[-1].bar_time,
            structure_score=structure.quality_score,
            breakout_strength=(breakout.close - structure.upper) / structure.upper,
            volume_ratio=Decimal(breakout.volume) / Decimal(structure.platform_avg_volume),
            wyckoff=wyckoff,
        )

    def _failed_signal(
        self,
        structure: ThirdBuyStructure,
        breakout: BreakoutBar,
        signal_time: datetime,
        failure_reason: str,
        forecast: str,
    ) -> ThirdBuySignal:
        breakout_strength = (breakout.close - structure.upper) / structure.upper
        volume_ratio = Decimal(breakout.volume) / Decimal(structure.platform_avg_volume)
        return ThirdBuySignal(
            ts_code=structure.ts_code,
            state="failed_3buy",
            action="filter",
            signal_time=signal_time,
            structure_score=structure.quality_score,
            breakout_strength=breakout_strength,
            volume_ratio=volume_ratio,
            wyckoff=WyckoffAssessment(
                background="supply_returned" if "volume" in failure_reason else "confirmation_failed",
                features={
                    "failure_reason": failure_reason,
                    "breakout_volume_ratio": f"{volume_ratio:.2f}",
                },
                forecast=forecast,
                score=25,
            ),
        )

    def _touches_upper_support(self, structure: ThirdBuyStructure, bar: PullbackBar) -> bool:
        tolerance = max(bar.atr * Decimal("0.50"), structure.upper * Decimal("0.02"))
        return bar.low <= structure.upper + tolerance and bar.low >= structure.upper - tolerance

    def _wyckoff_for_breakout(
        self,
        structure: ThirdBuyStructure,
        breakout_strength: Decimal,
        volume_ratio: Decimal,
    ) -> WyckoffAssessment:
        score = 45
        if structure.quality_score >= 80:
            score += 15
            background = "constructive"
        else:
            score += 8
            background = "acceptable"

        if volume_ratio >= Decimal("1.8"):
            score += 15
            volume_expansion = "confirmed"
        else:
            score += 8
            volume_expansion = "adequate"

        if breakout_strength >= Decimal("0.025"):
            score += 12
            close_quality = "strong_close_above_upper"
        else:
            score += 6
            close_quality = "close_above_upper"

        score = max(0, min(100, score))
        return WyckoffAssessment(
            background=background,
            features={
                "volume_expansion": volume_expansion,
                "close_quality": close_quality,
            },
            forecast="wait_pullback_confirmation",
            score=score,
        )

    def _wyckoff_for_confirmed_pullback(
        self,
        structure: ThirdBuyStructure,
        breakout: BreakoutBar,
        pullbacks: list[PullbackBar],
    ) -> WyckoffAssessment:
        breakout_strength = (breakout.close - structure.upper) / structure.upper
        volume_ratio = Decimal(breakout.volume) / Decimal(structure.platform_avg_volume)
        base = self._wyckoff_for_breakout(structure, breakout_strength, volume_ratio)
        score = min(100, base.score + 12)
        return WyckoffAssessment(
            background=base.background,
            features={
                **base.features,
                "pullback_volume": "shrinking",
                "support_quality": "accepted_above_upper",
                "pullback_window": f"{len(pullbacks)}_bars",
            },
            forecast="continuation_expected",
            score=score,
        )
