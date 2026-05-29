export type DashboardSignalState = "proto_3buy" | "confirmed_3buy" | "failed_3buy";
export type DashboardAction = "light_position" | "upgrade_position" | "observe" | "filter";

export type DashboardSignal = {
  ts_code: string;
  name: string;
  theme: string;
  state: DashboardSignalState;
  score: number;
  suggested_action: DashboardAction;
  amount: number;
  evidence: {
    structure: string;
    volume_price: string;
    wyckoff_forecast: string;
  };
};

export type DashboardSnapshot = {
  trade_date: string;
  market_regime: {
    state: "risk_on" | "neutral" | "risk_off";
    attack_allowed: boolean;
    suppress_new_signals: boolean;
    recommended_exposure_pct: number;
    evidence: string[];
  };
  mainlines: Array<{
    theme_code: string;
    theme: string;
    label: string;
    strength_score: number;
    amount_expansion: string;
    core_stocks: Array<{
      rank: number;
      ts_code: string;
      name: string;
      score: number;
    }>;
  }>;
  signals: DashboardSignal[];
  filters: {
    themes: string[];
    states: DashboardSignalState[];
    score_floor: number[];
  };
};

export const fallbackDashboard: DashboardSnapshot = {
  trade_date: "2026-05-26",
  market_regime: {
    state: "neutral",
    attack_allowed: true,
    suppress_new_signals: false,
    recommended_exposure_pct: 45,
    evidence: [
      "index_repair_without_full_risk_on",
      "breadth_improving_but_not_expanding",
      "confirmed_mainline_required",
    ],
  },
  mainlines: [
    {
      theme_code: "BK1234",
      theme: "机器人",
      label: "confirmed_mainline",
      strength_score: 88,
      amount_expansion: "1.62x",
      core_stocks: [
        { rank: 1, ts_code: "600001.SH", name: "机器人核心 Alpha", score: 91 },
        { rank: 2, ts_code: "600002.SH", name: "机器人跟踪 Delta", score: 83 },
      ],
    },
    {
      theme_code: "BK5678",
      theme: "CPO",
      label: "emerging_leader",
      strength_score: 79,
      amount_expansion: "1.31x",
      core_stocks: [{ rank: 1, ts_code: "600010.SH", name: "CPO 核心 Beta", score: 86 }],
    },
  ],
  signals: [
    {
      ts_code: "600001.SH",
      name: "机器人核心 Alpha",
      theme: "机器人",
      state: "confirmed_3buy",
      score: 86,
      suggested_action: "upgrade_position",
      amount: 200000000,
      evidence: {
        structure: "30m_platform_upper_breakout",
        volume_price: "breakout_expansion_pullback_shrinking",
        wyckoff_forecast: "continuation_expected",
      },
    },
    {
      ts_code: "600010.SH",
      name: "CPO 核心 Beta",
      theme: "CPO",
      state: "proto_3buy",
      score: 78,
      suggested_action: "light_position",
      amount: 160000000,
      evidence: {
        structure: "close_above_platform_upper",
        volume_price: "breakout_volume_confirmed",
        wyckoff_forecast: "wait_pullback_confirmation",
      },
    },
    {
      ts_code: "600020.SH",
      name: "算力观察 Gamma",
      theme: "算力",
      state: "failed_3buy",
      score: 41,
      suggested_action: "filter",
      amount: 90000000,
      evidence: {
        structure: "fell_back_inside_platform",
        volume_price: "supply_returned_on_volume",
        wyckoff_forecast: "supply_returned",
      },
    },
  ],
  filters: {
    themes: ["机器人", "CPO", "算力"],
    states: ["proto_3buy", "confirmed_3buy", "failed_3buy"],
    score_floor: [40, 60, 80],
  },
};

export async function fetchDashboardSnapshot(): Promise<DashboardSnapshot> {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
  const response = await fetch(`${baseUrl}/api/dashboard`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Dashboard request failed: ${response.status}`);
  }
  return response.json() as Promise<DashboardSnapshot>;
}
