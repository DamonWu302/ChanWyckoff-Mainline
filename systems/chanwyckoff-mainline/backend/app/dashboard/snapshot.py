def build_operations_snapshot() -> dict[str, object]:
    return {
        "trade_date": "2026-05-26",
        "market_regime": {
            "state": "neutral",
            "attack_allowed": True,
            "suppress_new_signals": False,
            "recommended_exposure_pct": 45,
            "evidence": [
                "index_repair_without_full_risk_on",
                "breadth_improving_but_not_expanding",
                "confirmed_mainline_required",
            ],
        },
        "mainlines": [
            {
                "theme": "机器人",
                "label": "confirmed_mainline",
                "strength_score": 88,
                "amount_expansion": "1.62x",
                "core_stocks": [
                    {"rank": 1, "ts_code": "600001.SH", "name": "机器人核心 Alpha", "score": 91},
                    {"rank": 2, "ts_code": "600002.SH", "name": "机器人跟踪 Delta", "score": 83},
                ],
            },
            {
                "theme": "CPO",
                "label": "emerging_leader",
                "strength_score": 79,
                "amount_expansion": "1.31x",
                "core_stocks": [
                    {"rank": 1, "ts_code": "600010.SH", "name": "CPO 核心 Beta", "score": 86},
                ],
            },
        ],
        "signals": [
            {
                "ts_code": "600001.SH",
                "name": "机器人核心 Alpha",
                "theme": "机器人",
                "state": "confirmed_3buy",
                "score": 86,
                "suggested_action": "upgrade_position",
                "amount": 200000000,
                "evidence": {
                    "structure": "30m_platform_upper_breakout",
                    "volume_price": "breakout_expansion_pullback_shrinking",
                    "wyckoff_forecast": "continuation_expected",
                },
            },
            {
                "ts_code": "600010.SH",
                "name": "CPO 核心 Beta",
                "theme": "CPO",
                "state": "proto_3buy",
                "score": 78,
                "suggested_action": "light_position",
                "amount": 160000000,
                "evidence": {
                    "structure": "close_above_platform_upper",
                    "volume_price": "breakout_volume_confirmed",
                    "wyckoff_forecast": "wait_pullback_confirmation",
                },
            },
            {
                "ts_code": "600020.SH",
                "name": "算力观察 Gamma",
                "theme": "算力",
                "state": "failed_3buy",
                "score": 41,
                "suggested_action": "filter",
                "amount": 90000000,
                "evidence": {
                    "structure": "fell_back_inside_platform",
                    "volume_price": "supply_returned_on_volume",
                    "wyckoff_forecast": "supply_returned",
                },
            },
        ],
        "filters": {
            "themes": ["机器人", "CPO", "算力"],
            "states": ["proto_3buy", "confirmed_3buy", "failed_3buy"],
            "score_floor": [40, 60, 80],
        },
    }
