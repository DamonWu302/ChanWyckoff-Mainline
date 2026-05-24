import type { CSSProperties } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { PageHeader } from "@/components/layout/PageHeader";
import { ButtonLink } from "@/components/ui/Button";
import { StructureChart } from "@/components/ui/Charts";
import { Panel } from "@/components/ui/Panel";
import { Status } from "@/components/ui/Status";

export function SignalDetailPage() {
  return (
    <AppShell note="展示价格时区分前复权分析价与真实操作价，避免除权结构和执行报价混淆。">
      <PageHeader
        actions={
          <>
            <Status variant="warn">market neutral</Status>
            <Status variant="good">wyckoff 86</Status>
            <ButtonLink href="/review" variant="primary">记录人工状态</ButtonLink>
          </>
        }
        eyebrow="Signal Detail"
        lead="这页把 30 分钟平台/中枢、突破、回踩、止损、目标和威科夫证据放到同一个解释面板里，帮助用户判断为什么它进入候选池。"
        title="机器人核心 Alpha · confirmed_3buy"
      />

      <section className="grid detail">
        <Panel action={<Status variant="good">confirmed_3buy</Status>} title="30 分钟结构图">
          <StructureChart />
        </Panel>

        <div className="stack">
          <Panel action={<Status variant="good">valid</Status>} title="信号状态机">
            <ul className="rule-list">
              <li><span className="mono subtle">proto</span><span>30 分钟收盘站上中枢上沿，成交额相对平台均量扩张。</span></li>
              <li><span className="mono subtle">pullback</span><span>1-8 根 30m 回踩落入容忍区，未有效回到中枢内部。</span></li>
              <li><span className="mono subtle">confirm</span><span>回踩阶段缩量，支撑行为健康，升级 confirmed_3buy。</span></li>
            </ul>
          </Panel>

          <Panel action={<Status variant="good">86</Status>} title="威科夫评分">
            <div className="split">
              <div className="score-ring" style={{ "--score": "86%" } as CSSProperties}>86</div>
              <ul className="rule-list signal-score-list">
                <li><span className="mono subtle">背景</span><span>主线处于 confirmed_mainline，个股为趋势容量核心。</span></li>
                <li><span className="mono subtle">特征</span><span>突破主动成交放大，回踩供应收缩。</span></li>
                <li><span className="mono subtle">预判</span><span>只影响优先级与仓位等级，不独立触发买卖。</span></li>
              </ul>
            </div>
          </Panel>

          <Panel action={<Status variant="warn">bounded</Status>} title="仓位与风控">
            <ul className="rule-list">
              <li><span className="mono subtle">position</span><span>confirmed 示例建议 20%-25%，受总仓位与主题暴露上限约束。</span></li>
              <li><span className="mono subtle">theme cap</span><span>同主题暴露不超过 50%-60%。</span></li>
              <li><span className="mono subtle">exit</span><span>结构失败止损、分段止盈、时间止损共同生效。</span></li>
            </ul>
          </Panel>
        </div>
      </section>
    </AppShell>
  );
}
