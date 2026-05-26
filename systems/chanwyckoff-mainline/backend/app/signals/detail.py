from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class SignalDetail:
    ts_code: str
    name: str
    theme: str
    state: str
    suggested_action: str
    score: int
    structure: dict[str, str | int]
    price_volume: dict[str, str]
    wyckoff: dict[str, object]
    risk: dict[str, object]


class SignalDetailService:
    def get_detail(self, ts_code: str) -> SignalDetail | None:
        return _SAMPLE_DETAILS.get(ts_code)


def detail_to_dict(detail: SignalDetail) -> dict[str, object]:
    return {
        "ts_code": detail.ts_code,
        "name": detail.name,
        "theme": detail.theme,
        "state": detail.state,
        "suggested_action": detail.suggested_action,
        "score": detail.score,
        "structure": detail.structure,
        "price_volume": detail.price_volume,
        "wyckoff": detail.wyckoff,
        "risk": detail.risk,
    }


def _money(value: Decimal) -> str:
    return f"{value:.4f}"


_SAMPLE_DETAILS = {
    "600001.SH": SignalDetail(
        ts_code="600001.SH",
        name="机器人核心 Alpha",
        theme="机器人",
        state="confirmed_3buy",
        suggested_action="upgrade_position",
        score=86,
        structure={
            "label": "statistical_platform",
            "upper": _money(Decimal("10.60")),
            "lower": _money(Decimal("9.80")),
            "mid": _money(Decimal("10.20")),
            "duration_bars": 18,
            "quality_score": 82,
            "upper_tests": 3,
        },
        price_volume={
            "breakout_close": _money(Decimal("10.95")),
            "breakout_strength": "3.30%",
            "breakout_volume_ratio": "1.85",
            "pullback_volume": "shrinking",
            "support_quality": "accepted_above_upper",
        },
        wyckoff={
            "background": "constructive",
            "features": [
                "volume_expansion_confirmed",
                "strong_close_above_upper",
                "pullback_supply_shrinking",
            ],
            "forecast": "continuation_expected",
            "score": 86,
        },
        risk={
            "position_pct": 25,
            "stop_loss": _money(Decimal("9.80")),
            "target_price": _money(Decimal("11.40")),
            "time_stop_bars": 8,
            "invalidations": [
                "close_back_inside_structure",
                "heavy_volume_supply_return",
                "pullback_timeout",
            ],
        },
    )
}
