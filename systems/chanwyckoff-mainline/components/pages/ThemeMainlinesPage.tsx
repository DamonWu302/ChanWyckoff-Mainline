"use client";

import Link from "next/link";
import { useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { PageHeader } from "@/components/layout/PageHeader";
import { MiniChart } from "@/components/ui/Charts";
import { Metric } from "@/components/ui/Metric";
import { Panel } from "@/components/ui/Panel";
import { Status } from "@/components/ui/Status";
import { cn } from "@/lib/cn";

const themeCards = [
  {
    title: "机器人",
    status: "confirmed_mainline",
    variant: "good" as const,
    line: undefined,
    rules: [
      ["resilience", "指数下跌时相对强度保持在主题队列前列。"],
      ["leadership", "指数修复时核心票先于板块扩散。"],
      ["turnover", "成交额连续扩张，排除单日新闻脉冲。"],
    ],
  },
  {
    title: "CPO",
    status: "emerging_leader",
    variant: "info" as const,
    line: "polygon(0 78%,12% 76%,25% 70%,38% 58%,51% 63%,67% 44%,84% 36%,100% 29%,100% 100%,0 100%)",
    rules: [
      ["resilience", "抗跌出现，但尚未完成跨阶段确认。"],
      ["leadership", "核心票已有领先，扩散广度仍需观察。"],
      ["turnover", "成交额放大但连续性未满规则窗口。"],
    ],
  },
  {
    title: "算力",
    status: "resistant_theme",
    variant: "warn" as const,
    line: "polygon(0 60%,14% 54%,27% 62%,40% 57%,55% 49%,72% 58%,88% 56%,100% 52%,100% 100%,0 100%)",
    rules: [
      ["resilience", "下跌阶段抗跌成立。"],
      ["leadership", "反弹领涨未确认，不提高仓位级别。"],
      ["risk", "失败信号进入复盘队列，不进入普通候选。"],
    ],
  },
];

export function ThemeMainlinesPage() {
  const [active, setActive] = useState<"theme" | "rank">("theme");

  return (
    <AppShell note="题材归因以概念/主题优先，行业作为容量和业务背景，不参与主线主标签抢占。">
      <PageHeader
        actions={
          <div className="tabs">
            <button className={cn("tab", active === "theme" && "active")} onClick={() => setActive("theme")} type="button">题材状态</button>
            <button className={cn("tab", active === "rank" && "active")} onClick={() => setActive("rank")} type="button">核心排序</button>
          </div>
        }
        eyebrow="Theme Mainlines"
        lead="页面用于判断题材是否从抗跌走向领涨，并在主题内部排序核心票，避免把后排一日脉冲误判成主线机会。"
        title="穿越主线与趋势容量核心"
      />
      {active === "theme" ? <ThemeState /> : <CoreRank />}
    </AppShell>
  );
}

function ThemeState() {
  return (
    <>
      <section className="grid cols-3 section-gap">
        <Metric foot="机器人主线确认" label="Lifecycle" value="confirmed" />
        <Metric foot="AkShare 作为首版采集入口" label="Primary provider" value="Eastmoney" />
        <Metric foot="本地保存每日题材快照" label="Snapshot" value="D+0" />
      </section>
      <div className="grid cols-3">
        {themeCards.map((card) => (
          <Panel action={<Status variant={card.variant}>{card.status}</Status>} bodyClassName="stack" key={card.title} title={card.title}>
            <MiniChart lineStyle={card.line} />
            <ul className="rule-list">
              {card.rules.map(([label, body]) => (
                <li key={label}><span className="mono subtle">{label}</span><span>{body}</span></li>
              ))}
            </ul>
          </Panel>
        ))}
      </div>
    </>
  );
}

function CoreRank() {
  const rows = [
    ["#1", "机器人核心 Alpha", "自动化设备", "机器人", "good", "高", "合格", "领先", "强", "优", "/signal-detail", "看 30m 结构"],
    ["#2", "CPO 核心 Beta", "通信设备", "CPO", "info", "中高", "合格", "领先", "中", "良", "/signal-detail", "看 30m 结构"],
    ["#3", "机器人跟踪 Delta", "专用设备", "机器人", "good", "中", "合格", "跟随", "强", "良", "/today-operations", "回候选池"],
  ] as const;

  return (
    <Panel action={<Status>5-factor ranker</Status>} bodyClassName="table-panel-body" title="趋势容量核心排序">
      <div className="table-wrap">
        <table>
          <thead><tr><th>排名</th><th>股票</th><th>主归因</th><th>相对强度</th><th>容量</th><th>领先性</th><th>抗跌</th><th>结构质量</th><th>下一步</th></tr></thead>
          <tbody>
            {rows.map(([rank, stock, industry, theme, variant, strength, capacity, lead, resilience, structure, href, action]) => (
              <tr key={stock}>
                <td className="mono">{rank}</td>
                <td><strong>{stock}</strong><div className="subtle">行业：{industry}</div></td>
                <td><Status variant={variant as "good" | "info"}>{theme}</Status></td>
                <td className="mono">{strength}</td>
                <td className="mono">{capacity}</td>
                <td className="mono">{lead}</td>
                <td className="mono">{resilience}</td>
                <td className="mono">{structure}</td>
                <td><Link className="link-button" href={href}>{action}</Link></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Panel>
  );
}
