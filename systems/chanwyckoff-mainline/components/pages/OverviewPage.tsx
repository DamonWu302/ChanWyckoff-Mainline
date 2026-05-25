import Link from "next/link";
import { AppShell } from "@/components/layout/AppShell";
import { PageHeader } from "@/components/layout/PageHeader";
import { ButtonLink } from "@/components/ui/Button";
import { Panel } from "@/components/ui/Panel";
import { Status } from "@/components/ui/Status";
import { BackendHealth } from "@/components/system/BackendHealth";

const chain = [
  ["大盘环境", "risk_on / neutral / risk_off 作为最高交易闸门"],
  ["题材主线", "抗跌、领涨、成交额持续扩张"],
  ["趋势容量核心", "强度、容量、领先性、抗跌、结构质量"],
  ["30 分钟结构", "工程中枢优先，统计平台兜底"],
  ["工程化三买", "proto / confirmed / failed 状态机"],
  ["仓位风控", "个股、题材、总仓位三层约束"],
];

const screens = [
  {
    href: "/today-operations",
    status: "Primary",
    variant: "good" as const,
    title: "今日作战台",
    body: "把市场闸门、主线、核心票、三买候选和建议动作放在同一屏，支持按主题、分数和状态筛选。",
    foot: "primary workspace",
  },
  {
    href: "/theme-mainlines",
    status: "Drilldown",
    variant: "info" as const,
    title: "题材主线",
    body: "突出概念优先、行业背景辅助，比较主线生命周期与趋势容量核心排序。",
    foot: "theme engine",
  },
  {
    href: "/signal-detail",
    status: "Structure",
    variant: "warn" as const,
    title: "信号详情",
    body: "连接 30 分钟中枢、突破线、回踩区、止损区、目标线和威科夫三段解释。",
    foot: "structure inspector",
  },
  {
    href: "/backtest",
    status: "Research",
    variant: "info" as const,
    title: "回测稳健性",
    body: "不只显示权益曲线，还验证评分分层、proto 与 confirmed 的差异、年度和市场阶段切片。",
    foot: "research report",
  },
  {
    href: "/review",
    status: "Human loop",
    variant: "default" as const,
    title: "复盘记录",
    body: "保留规则输出、人工状态、失败归因和交易备注，让候选能进入可追踪的计划闭环。",
    foot: "human loop",
  },
];

export function OverviewPage() {
  return (
    <AppShell note="第一阶段是决策辅助系统：规则化信号决定候选与仓位，LLM 只负责解释、复盘和失败样本归纳。">
      <PageHeader
        actions={
          <>
            <BackendHealth />
            <ButtonLink href="/today-operations" variant="primary">进入今日作战台</ButtonLink>
          </>
        }
        eyebrow="Desktop operations"
        lead="系统按核心链路组织桌面工作区：大盘环境、题材主线、趋势容量核心、30 分钟结构、工程化三买、仓位风控、回测与复盘。"
        title="缠威主线系统：从大盘到三买信号的操作工作台"
      />

      <Panel
        action={<Status variant="good">rule based</Status>}
        className="overview-decision-panel"
        title="决策链路"
      >
        <div className="decision-chain">
          {chain.map(([title, body]) => (
            <div className="chain-step" key={title}>
              <strong>{title}</strong>
              <span>{body}</span>
            </div>
          ))}
        </div>
      </Panel>

      <section className="launcher-grid">
        {screens.map((screen) => (
          <Link className="screen-card" href={screen.href} key={screen.href}>
            <Status variant={screen.variant}>{screen.status}</Status>
            <div>
              <h2>{screen.title}</h2>
              <p>{screen.body}</p>
            </div>
            <span className="mono">{screen.foot}</span>
          </Link>
        ))}
      </section>
    </AppShell>
  );
}
