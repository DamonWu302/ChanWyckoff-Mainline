export type SignalDetail = {
  ts_code: string;
  name: string;
  theme: string;
  state: "proto_3buy" | "confirmed_3buy" | "failed_3buy";
  suggested_action: "light_position" | "upgrade_position" | "observe" | "filter";
  score: number;
  structure: {
    label: string;
    upper: string;
    lower: string;
    mid: string;
    duration_bars: number;
    quality_score: number;
    upper_tests: number;
  };
  price_volume: {
    breakout_close: string;
    breakout_strength: string;
    breakout_volume_ratio: string;
    pullback_volume: string;
    support_quality: string;
  };
  wyckoff: {
    background: string;
    features: string[];
    forecast: string;
    score: number;
  };
  risk: {
    position_pct: number;
    stop_loss: string;
    target_price: string;
    time_stop_bars: number;
    invalidations: string[];
  };
};

export const fallbackSignalDetail: SignalDetail = {
  ts_code: "600001.SH",
  name: "机器人核心 Alpha",
  theme: "机器人",
  state: "confirmed_3buy",
  suggested_action: "upgrade_position",
  score: 86,
  structure: {
    label: "statistical_platform",
    upper: "10.6000",
    lower: "9.8000",
    mid: "10.2000",
    duration_bars: 18,
    quality_score: 82,
    upper_tests: 3,
  },
  price_volume: {
    breakout_close: "10.9500",
    breakout_strength: "3.30%",
    breakout_volume_ratio: "1.85",
    pullback_volume: "shrinking",
    support_quality: "accepted_above_upper",
  },
  wyckoff: {
    background: "constructive",
    features: [
      "volume_expansion_confirmed",
      "strong_close_above_upper",
      "pullback_supply_shrinking",
    ],
    forecast: "continuation_expected",
    score: 86,
  },
  risk: {
    position_pct: 25,
    stop_loss: "9.8000",
    target_price: "11.4000",
    time_stop_bars: 8,
    invalidations: [
      "close_back_inside_structure",
      "heavy_volume_supply_return",
      "pullback_timeout",
    ],
  },
};

export async function fetchSignalDetail(tsCode = "600001.SH"): Promise<SignalDetail> {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
  const response = await fetch(`${baseUrl}/api/signals/${tsCode}/detail`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Signal detail request failed: ${response.status}`);
  }
  return response.json() as Promise<SignalDetail>;
}
