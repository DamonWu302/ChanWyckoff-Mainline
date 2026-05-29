"use client";

import { useEffect, useMemo, useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { PageHeader } from "@/components/layout/PageHeader";
import { MiniChart } from "@/components/ui/Charts";
import { CopyButton } from "@/components/ui/CopyButton";
import { Metric } from "@/components/ui/Metric";
import { Panel } from "@/components/ui/Panel";
import { Status } from "@/components/ui/Status";
import {
  fallbackBacktestSummary,
  fetchBacktestSummary,
  type BacktestSummary,
} from "@/lib/backtestSummary";

export function BacktestPage() {
  const [summary, setSummary] = useState<BacktestSummary>(fallbackBacktestSummary);
  const best = summary.best ?? summary.results[0];
  const bucketRows = useMemo(() => {
    return Object.entries(best?.by_wyckoff_bucket ?? {}).sort(([left], [right]) => right.localeCompare(left));
  }, [best]);

  useEffect(() => {
    let mounted = true;
    fetchBacktestSummary()
      .then((nextSummary) => {
        if (mounted) setSummary(nextSummary);
      })
      .catch(() => {
        if (mounted) setSummary(fallbackBacktestSummary);
      });
    return () => {
      mounted = false;
    };
  }, []);

  return (
    <AppShell note="主题增强回测只在历史主题数据可靠区间内给结论，结构回测从 2019 起独立验证。">
      <PageHeader
        actions={<CopyButton text="Structural backtest: cost + slippage + limit-up/down + suspension + capacity constraints">复制回测约束</CopyButton>}
        eyebrow="Backtest Robustness"
        lead="该页面强调“证明规则有效”而不是只展示一条权益曲线：按分数、状态、年份、市场阶段、主题和个股贡献拆开看。"
        title="评分分层与确认价值验证"
      />

      <section className="grid cols-4 section-gap">
        <Metric foot="先验证三买结构本体" label="Mode" value="structural" />
        <Metric foot={summary.end.slice(0, 10)} label="Window" value={summary.start.slice(0, 10)} />
        <Metric foot="含成本、滑点、停复牌约束" label="Execution" value="next bar" />
        <Metric foot={best?.risk_flags.join(" / ") || "no flags"} label="Search" value={best?.name ?? "small grid"} />
      </section>

      <section className="grid cols-2">
        <Panel action={<Status variant="info">API</Status>} title="权益与回撤">
          <MiniChart className="backtest-equity-chart" lineStyle="polygon(0 82%,10% 70%,20% 74%,31% 55%,42% 59%,53% 40%,64% 46%,75% 24%,87% 34%,100% 18%,100% 100%,0 100%)" />
          <ul className="rule-list">
            <li><span className="mono subtle">trades</span><span>{best?.total_trades ?? 0} 笔，胜率 {best?.win_rate ?? "0"}</span></li>
            <li><span className="mono subtle">return</span><span>均值 {best?.mean_return ?? "0"} / 中位 {best?.median_return ?? "0"}</span></li>
            <li><span className="mono subtle">drawdown</span><span>最大回撤 {best?.max_drawdown ?? "0"}</span></li>
          </ul>
        </Panel>

        <Panel action={<Status variant="good">must prove</Status>} bodyClassName="table-panel-body" title="评分分层">
          <div className="table-wrap">
            <table>
              <thead><tr><th>层级</th><th>规则含义</th><th>样本</th><th>结论状态</th></tr></thead>
              <tbody>
                {bucketRows.map(([bucket, slice]) => (
                  <tr key={bucket}>
                    <td className="mono">{bucket}</td>
                    <td>按 wyckoff_score 分段验证</td>
                    <td className="mono">{slice.total_trades}</td>
                    <td><Status variant={Number(slice.mean_return) > 0 ? "good" : "warn"}>{slice.mean_return}</Status></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>

        <Panel action={<Status variant="info">comparison</Status>} title="proto vs confirmed">
          <ul className="rule-list">
            <li><span className="mono subtle">proto</span><span>优秀突破后轻仓探测，验证是否提高早期参与收益。</span></li>
            <li><span className="mono subtle">confirmed</span><span>等待回踩确认，验证是否降低失败率和回撤。</span></li>
            <li><span className="mono subtle">delta</span><span>{Object.entries(best?.by_signal_state ?? {}).map(([state, item]) => `${state}: ${item.mean_return}`).join(" / ")}</span></li>
          </ul>
        </Panel>

        <Panel action={<Status>slices</Status>} title="稳健性切片">
          <div className="decision-chain robustness-chain">
            <div className="chain-step"><strong>参数</strong><span>{summary.results.map((item) => `${item.name}:${item.parameters.max_holding_bars}`).join(" / ")}</span></div>
            <div className="chain-step"><strong>集中度</strong><span>{Object.entries(best?.symbol_concentration ?? {}).map(([symbol, value]) => `${symbol} ${value}`).join(" / ")}</span></div>
            <div className="chain-step"><strong>可靠性</strong><span>{summary.reliability_note}</span></div>
          </div>
        </Panel>
      </section>
    </AppShell>
  );
}
