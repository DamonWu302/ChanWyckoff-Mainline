"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button, ButtonLink } from "@/components/ui/Button";
import { MiniChart } from "@/components/ui/Charts";
import { Metric } from "@/components/ui/Metric";
import { Panel } from "@/components/ui/Panel";
import { Status } from "@/components/ui/Status";
import {
  type DashboardSignal,
  fallbackDashboard,
  fetchDashboardSnapshot,
} from "@/lib/dashboard";

type DrawerSignal = DashboardSignal | null;

function signalVariant(state: DashboardSignal["state"]) {
  if (state === "confirmed_3buy") return "good";
  if (state === "failed_3buy") return "danger";
  return "info";
}

function themeVariant(index: number) {
  return index === 0 ? "good" : index === 1 ? "info" : "warn";
}

function formatAmount(amount: number) {
  return `${(amount / 100000000).toFixed(1)} 亿`;
}

const evidenceText: Record<string, string> = {
  index_repair_without_full_risk_on: "指数修复，但尚未进入完整 risk_on",
  breadth_improving_but_not_expanding: "赚钱效应改善，扩散强度仍需确认",
  confirmed_mainline_required: "只处理确认主线与核心票信号",
  breakout_expansion_pullback_shrinking: "突破放量，回踩缩量承接",
  breakout_volume_confirmed: "突破量能确认，等待回踩",
  supply_returned_on_volume: "供应带量重回结构内",
};

function labelEvidence(value: string) {
  return evidenceText[value] ?? value;
}

export function TodayOperationsPage() {
  const [snapshot, setSnapshot] = useState(fallbackDashboard);
  const [theme, setTheme] = useState("all");
  const [stage, setStage] = useState("all");
  const [score, setScore] = useState("all");
  const [drawerSignal, setDrawerSignal] = useState<DrawerSignal>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    let mounted = true;
    fetchDashboardSnapshot()
      .then((nextSnapshot) => {
        if (mounted) setSnapshot(nextSnapshot);
      })
      .catch(() => {
        if (mounted) setSnapshot(fallbackDashboard);
      });
    return () => {
      mounted = false;
    };
  }, []);

  const filtered = useMemo(() => {
    return snapshot.signals.filter((candidate) => {
      const themeOk = theme === "all" || candidate.theme === theme;
      const stageOk = stage === "all" || candidate.state === stage;
      const minScore = score === "all" ? 0 : Number(score);
      return themeOk && stageOk && candidate.score >= minScore;
    });
  }, [snapshot.signals, theme, stage, score]);

  async function copyRule() {
    const text = "risk_on -> confirmed_mainline -> core_rank <= 3 -> confirmed_3buy -> risk cap";
    if (navigator.clipboard) {
      await navigator.clipboard.writeText(text);
    }
    setCopied(true);
    window.setTimeout(() => setCopied(false), 900);
  }

  return (
    <AppShell note="普通新仓受大盘闸门约束；risk_off 下只保留极少数穿越主线观察，不直接放大仓位。">
      <PageHeader
        actions={
          <>
            <Button className={copied ? "is-copied" : undefined} onClick={copyRule} type="button">
              {copied ? "已复制" : "复制作战规则"}
            </Button>
            <ButtonLink href="/signal-detail" variant="primary">查看信号详情</ButtonLink>
          </>
        }
        eyebrow="Today Operations"
        lead="先看大盘是否允许进攻，再看穿越主线与核心票，最后处理 30 分钟三买候选。表格由规则引擎输出，按每日数据快照与 30 分钟扫描刷新。"
        title="今日作战台"
      />

      <section className="grid cols-4 section-gap">
        <Metric
          foot={snapshot.market_regime.attack_allowed ? "允许主线核心参与" : "新信号压制"}
          label="Market regime"
          value={snapshot.market_regime.state}
        />
        <Metric foot={`交易日 ${snapshot.trade_date}`} label="Active mainlines" value={String(snapshot.mainlines.length)} />
        <Metric foot="按筛选实时更新" label="3buy candidates" value={String(filtered.length)} />
        <Metric
          foot={`${snapshot.market_regime.state} 下总仓位上限`}
          label="Exposure gate"
          value={`≤ ${snapshot.market_regime.recommended_exposure_pct}%`}
        />
      </section>

      <section className="grid ops today-workspace">
        <div className="ops-side">
          <Panel action={<Status variant="warn">{snapshot.market_regime.state}</Status>} bodyClassName="stack" title="大盘闸门">
            <MiniChart />
            <ul className="rule-list">
              {snapshot.market_regime.evidence.map((item) => (
                <li key={item}><span className="mono subtle">gate</span><span>{labelEvidence(item)}</span></li>
              ))}
            </ul>
          </Panel>

          <Panel action={<Link className="link-button" href="/theme-mainlines">钻取</Link>} bodyClassName="mainline-list" title="主线队列">
            {snapshot.mainlines.map((mainline) => (
              <div className="mainline-item" key={mainline.theme}>
                <div className="mainline-meta">{mainline.label}</div>
                <strong>{mainline.theme}</strong>
                <p>强度 {mainline.strength_score}，成交额放大 {mainline.amount_expansion}</p>
                <p>{mainline.core_stocks.map((stock) => `#${stock.rank} ${stock.name}`).join(" / ")}</p>
              </div>
            ))}
          </Panel>
        </div>

        <section className="panel">
          <div className="panel-header">
            <h2>三买候选</h2>
            <div className="filters">
              <select aria-label="题材筛选" onChange={(event) => setTheme(event.target.value)} value={theme}>
                <option value="all">全部题材</option>
                {snapshot.filters.themes.map((item) => <option key={item} value={item}>{item}</option>)}
              </select>
              <select aria-label="状态筛选" onChange={(event) => setStage(event.target.value)} value={stage}>
                <option value="all">全部状态</option>
                {snapshot.filters.states.map((item) => <option key={item} value={item}>{item}</option>)}
              </select>
              <select aria-label="分数筛选" onChange={(event) => setScore(event.target.value)} value={score}>
                <option value="all">全部分数</option>
                {snapshot.filters.score_floor.map((item) => <option key={item} value={item}>≥{item}</option>)}
              </select>
            </div>
          </div>
          <div className="table-wrap ops-table-wrap">
            <table className="ops-table">
              <colgroup>
                <col className="col-stock" />
                <col className="col-theme" />
                <col className="col-stage" />
                <col className="col-score" />
                <col className="col-core" />
                <col className="col-evidence" />
                <col className="col-action" />
              </colgroup>
              <thead>
                <tr><th>股票</th><th>主线</th><th>状态</th><th>分数</th><th>成交额</th><th>量价证据</th><th>动作</th></tr>
              </thead>
              <tbody>
                {filtered.map((candidate) => (
                  <tr key={candidate.ts_code}>
                    <td><strong>{candidate.name}</strong><div className="subtle mono">{candidate.ts_code}</div></td>
                    <td><Status variant={themeVariant(snapshot.filters.themes.indexOf(candidate.theme))}>{candidate.theme}</Status></td>
                    <td><Status variant={signalVariant(candidate.state)}>{candidate.state}</Status></td>
                    <td className="mono">{candidate.score}</td>
                    <td className="mono">{formatAmount(candidate.amount)}</td>
                    <td className="evidence-cell">{labelEvidence(candidate.evidence.volume_price)}</td>
                    <td className="row-actions">
                      <Link className="link-button" href={candidate.state === "failed_3buy" ? "/review" : "/signal-detail"}>
                        {candidate.suggested_action}
                      </Link>
                      <button className="link-button" onClick={() => setDrawerSignal(candidate)} type="button">摘要</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </section>

      <aside aria-hidden={!drawerSignal} aria-label="信号摘要" className={`drawer ${drawerSignal ? "open" : ""}`}>
        <div className="panel-header">
          <div>
            <div className="eyebrow">Signal summary</div>
            <h2>{drawerSignal?.name ?? "信号摘要"}</h2>
          </div>
          <Button onClick={() => setDrawerSignal(null)} type="button" variant="ghost">关闭</Button>
        </div>
        <div className="drawer-content stack">
          <div className="split">
            <Status variant={drawerSignal ? signalVariant(drawerSignal.state) : "good"}>{drawerSignal?.state ?? "confirmed_3buy"}</Status>
            <Status variant={drawerSignal ? themeVariant(snapshot.filters.themes.indexOf(drawerSignal.theme)) : "info"}>
              {drawerSignal?.theme ?? "机器人"}
            </Status>
          </div>
          <ul className="rule-list">
            <li><span className="mono subtle">structure</span><span>{drawerSignal?.evidence.structure ?? "30m_platform_upper_breakout"}</span></li>
            <li><span className="mono subtle">price</span><span>{labelEvidence(drawerSignal?.evidence.volume_price ?? "breakout_expansion_pullback_shrinking")}</span></li>
            <li><span className="mono subtle">wyckoff</span><span>{drawerSignal?.evidence.wyckoff_forecast ?? "continuation_expected"}</span></li>
          </ul>
          <ButtonLink href="/signal-detail" variant="primary">打开完整结构</ButtonLink>
        </div>
      </aside>
    </AppShell>
  );
}
