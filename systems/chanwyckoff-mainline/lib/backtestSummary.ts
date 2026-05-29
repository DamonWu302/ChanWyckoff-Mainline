export type BacktestSlice = {
  total_trades: number;
  win_rate: string;
  mean_return: string;
  median_return: string;
};

export type BacktestGridResult = {
  name: string;
  parameters: {
    max_holding_bars: number;
  };
  total_trades: number;
  win_rate: string;
  mean_return: string;
  median_return: string;
  max_drawdown: string;
  risk_flags: string[];
  symbol_concentration: Record<string, string>;
  by_signal_state: Record<string, BacktestSlice>;
  by_wyckoff_bucket: Record<string, BacktestSlice>;
  skipped_signals: Array<{
    ts_code: string;
    theme: string | null;
    signal_state: string;
    signal_time: string;
    reason: string;
  }>;
};

export type BacktestSummary = {
  start: string;
  end: string;
  best: BacktestGridResult | null;
  results: BacktestGridResult[];
  reliability_note: string;
};

export const fallbackBacktestSummary: BacktestSummary = {
  start: "2026-05-25T10:00:00+00:00",
  end: "2026-05-27T10:00:00+00:00",
  best: null,
  results: [
    {
      name: "fast",
      parameters: { max_holding_bars: 1 },
      total_trades: 2,
      win_rate: "0.5",
      mean_return: "0.004",
      median_return: "0.004",
      max_drawdown: "0.026",
      risk_flags: ["small_sample", "symbol_concentration"],
      symbol_concentration: { "600001.SH": "0.5", "600010.SH": "0.5" },
      by_signal_state: {
        confirmed_3buy: { total_trades: 1, win_rate: "1", mean_return: "0.04", median_return: "0.04" },
        proto_3buy: { total_trades: 1, win_rate: "0", mean_return: "-0.03", median_return: "-0.03" },
      },
      by_wyckoff_bucket: {
        "80-100": { total_trades: 1, win_rate: "1", mean_return: "0.04", median_return: "0.04" },
        "60-79": { total_trades: 1, win_rate: "0", mean_return: "-0.03", median_return: "-0.03" },
      },
      skipped_signals: [],
    },
  ],
  reliability_note: "theme_history_reliability_requires_point_in_time_constituents",
};

export async function fetchBacktestSummary(): Promise<BacktestSummary> {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
  const response = await fetch(`${baseUrl}/api/backtests/summary`, {
    method: "POST",
    cache: "no-store",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      start: fallbackBacktestSummary.start,
      end: fallbackBacktestSummary.end,
      parameter_sets: [
        { name: "fast", max_holding_bars: 1 },
        { name: "patient", max_holding_bars: 8 },
      ],
    }),
  });
  if (!response.ok) {
    throw new Error(`Backtest summary request failed: ${response.status}`);
  }
  return response.json() as Promise<BacktestSummary>;
}
