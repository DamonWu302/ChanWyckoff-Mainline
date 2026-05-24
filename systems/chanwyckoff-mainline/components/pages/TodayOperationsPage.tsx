"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button, ButtonLink } from "@/components/ui/Button";
import { MiniChart } from "@/components/ui/Charts";
import { Metric } from "@/components/ui/Metric";
import { Panel } from "@/components/ui/Panel";
import { Status } from "@/components/ui/Status";

const candidates = [
  {
    stock: "机器人核心 Alpha",
    sub: "主板 / 前复权",
    themeKey: "robotics",
    theme: "机器人",
    themeVariant: "good" as const,
    stage: "confirmed_3buy",
    stageVariant: "good" as const,
    score: 86,
    core: "#1",
    evidence: "突破放量，回踩缩量，未有效回中枢",
    actionHref: "/signal-detail",
    actionLabel: "详情",
  },
  {
    stock: "CPO 核心 Beta",
    sub: "主板 / 前复权",
    themeKey: "cpo",
    theme: "CPO",
    themeVariant: "info" as const,
    stage: "proto_3buy",
    stageVariant: "info" as const,
    score: 78,
    core: "#2",
    evidence: "30 分钟收盘突破，上沿测试次数充足",
    actionHref: "/signal-detail",
    actionLabel: "详情",
  },
  {
    stock: "算力观察 Gamma",
    sub: "主板 / 前复权",
    themeKey: "compute",
    theme: "算力",
    themeVariant: "warn" as const,
    stage: "failed_3buy",
    stageVariant: "danger" as const,
    score: 41,
    core: "#5",
    evidence: "带量跌回中枢，供应重新进入",
    actionHref: "/review",
    actionLabel: "复盘",
  },
  {
    stock: "机器人跟踪 Delta",
    sub: "主板 / 前复权",
    themeKey: "robotics",
    theme: "机器人",
    themeVariant: "good" as const,
    stage: "proto_3buy",
    stageVariant: "info" as const,
    score: 64,
    core: "#3",
    evidence: "突破质量合格，等待 1-8 根 30m 回踩验证",
    actionHref: "/signal-detail",
    actionLabel: "详情",
  },
];

type DrawerSignal = (typeof candidates)[number] | null;

export function TodayOperationsPage() {
  const [theme, setTheme] = useState("all");
  const [stage, setStage] = useState("all");
  const [score, setScore] = useState("all");
  const [drawerSignal, setDrawerSignal] = useState<DrawerSignal>(null);
  const [copied, setCopied] = useState(false);

  const filtered = useMemo(() => {
    return candidates.filter((candidate) => {
      const themeOk = theme === "all" || candidate.themeKey === theme;
      const stageOk = stage === "all" || candidate.stage === stage;
      const minScore = score === "all" ? 0 : Number(score);
      return themeOk && stageOk && candidate.score >= minScore;
    });
  }, [theme, stage, score]);

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
        <Metric foot="进攻仓位需等待主线与结构共振" label="Market regime" value="neutral" />
        <Metric foot="confirmed 1 / emerging 2" label="Active mainlines" value="3" />
        <Metric foot="按筛选实时更新" label="3buy candidates" value={String(filtered.length)} />
        <Metric foot="neutral 下总仓位上限示例" label="Exposure gate" value="≤ 45%" />
      </section>

      <section className="grid ops today-workspace">
        <div className="ops-side">
          <Panel action={<Status variant="warn">neutral</Status>} bodyClassName="stack" title="大盘闸门">
            <MiniChart />
            <ul className="rule-list">
              <li><span className="mono subtle">index</span><span>上证 / 全 A 没有同步 risk_on，赚钱效应处于修复中。</span></li>
              <li><span className="mono subtle">breadth</span><span>上涨家数与成交额扩张未形成连续性。</span></li>
              <li><span className="mono subtle">gate</span><span>允许跟踪强主线确认信号，禁止普通后排追涨。</span></li>
            </ul>
          </Panel>

          <Panel action={<Link className="link-button" href="/theme-mainlines">钻取</Link>} bodyClassName="mainline-list" title="主线队列">
            {[
              ["confirmed_mainline", "机器人", "抗跌 + 转强领涨 + 成交额扩张"],
              ["emerging_leader", "CPO", "放量修复，核心票领先"],
              ["resistant_theme", "算力", "指数下跌抗跌，领涨未确认"],
            ].map(([meta, title, body]) => (
              <div className="mainline-item" key={title}>
                <div className="mainline-meta">{meta}</div>
                <strong>{title}</strong>
                <p>{body}</p>
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
                <option value="robotics">机器人</option>
                <option value="cpo">CPO</option>
                <option value="compute">算力</option>
              </select>
              <select aria-label="状态筛选" onChange={(event) => setStage(event.target.value)} value={stage}>
                <option value="all">全部状态</option>
                <option value="proto_3buy">proto_3buy</option>
                <option value="confirmed_3buy">confirmed_3buy</option>
                <option value="failed_3buy">failed_3buy</option>
              </select>
              <select aria-label="分数筛选" onChange={(event) => setScore(event.target.value)} value={score}>
                <option value="all">全部分数</option>
                <option value="80">≥80</option>
                <option value="60">≥60</option>
                <option value="40">≥40</option>
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
                <tr><th>股票</th><th>主线</th><th>状态</th><th>分数</th><th>核心</th><th>量价证据</th><th>动作</th></tr>
              </thead>
              <tbody>
                {filtered.map((candidate) => (
                  <tr key={candidate.stock}>
                    <td><strong>{candidate.stock}</strong><div className="subtle mono">{candidate.sub}</div></td>
                    <td><Status variant={candidate.themeVariant}>{candidate.theme}</Status></td>
                    <td><Status variant={candidate.stageVariant}>{candidate.stage}</Status></td>
                    <td className="mono">{candidate.score}</td>
                    <td className="mono">{candidate.core}</td>
                    <td className="evidence-cell">{candidate.evidence}</td>
                    <td className="row-actions">
                      <Link className="link-button" href={candidate.actionHref}>{candidate.actionLabel}</Link>
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
            <h2>{drawerSignal?.stock ?? "信号摘要"}</h2>
          </div>
          <Button onClick={() => setDrawerSignal(null)} type="button" variant="ghost">关闭</Button>
        </div>
        <div className="drawer-content stack">
          <div className="split">
            <Status variant={drawerSignal?.stageVariant ?? "good"}>{drawerSignal?.stage ?? "confirmed_3buy"}</Status>
            <Status variant={drawerSignal?.themeVariant ?? "info"}>{drawerSignal?.theme ?? "机器人"}</Status>
          </div>
          <ul className="rule-list">
            <li><span className="mono subtle">gate</span><span>neutral，只允许主线核心和高分结构进入计划。</span></li>
            <li><span className="mono subtle">risk</span><span>proto 约 10%，confirmed 20%-25%， exceptional 不超过单票 30%。</span></li>
            <li><span className="mono subtle">invalid</span><span>有效跌回中枢、供应带量重入或 1-8 根 30m 内确认失败。</span></li>
          </ul>
          <ButtonLink href="/signal-detail" variant="primary">打开完整结构</ButtonLink>
        </div>
      </aside>
    </AppShell>
  );
}

