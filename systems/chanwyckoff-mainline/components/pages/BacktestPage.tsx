import { AppShell } from "@/components/layout/AppShell";
import { PageHeader } from "@/components/layout/PageHeader";
import { MiniChart } from "@/components/ui/Charts";
import { CopyButton } from "@/components/ui/CopyButton";
import { Metric } from "@/components/ui/Metric";
import { Panel } from "@/components/ui/Panel";
import { Status } from "@/components/ui/Status";

export function BacktestPage() {
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
        <Metric foot="跨市场阶段切片" label="Window" value="2019+" />
        <Metric foot="含成本、滑点、停复牌约束" label="Execution" value="next bar" />
        <Metric foot="小范围稳健性，不做宽泛优化" label="Search" value="small grid" />
      </section>

      <section className="grid cols-2">
        <Panel action={<Status>待接入回测</Status>} title="权益与回撤">
          <MiniChart className="backtest-equity-chart" lineStyle="polygon(0 82%,10% 70%,20% 74%,31% 55%,42% 59%,53% 40%,64% 46%,75% 24%,87% 34%,100% 18%,100% 100%,0 100%)" />
        </Panel>

        <Panel action={<Status variant="good">must prove</Status>} bodyClassName="table-panel-body" title="评分分层">
          <div className="table-wrap">
            <table>
              <thead><tr><th>层级</th><th>规则含义</th><th>样本</th><th>结论状态</th></tr></thead>
              <tbody>
                <tr><td className="mono">80+</td><td>高质量机会，优先进入作战台</td><td className="mono">待接入</td><td><Status variant="warn">待验证</Status></td></tr>
                <tr><td className="mono">60-79</td><td>可观察，降低优先级</td><td className="mono">待接入</td><td><Status variant="warn">待验证</Status></td></tr>
                <tr><td className="mono">40-59</td><td>观察池，通常不交易</td><td className="mono">待接入</td><td><Status>记录</Status></td></tr>
                <tr><td className="mono">&lt;40</td><td>过滤出交易候选</td><td className="mono">待接入</td><td><Status variant="danger">过滤</Status></td></tr>
              </tbody>
            </table>
          </div>
        </Panel>

        <Panel action={<Status variant="info">comparison</Status>} title="proto vs confirmed">
          <ul className="rule-list">
            <li><span className="mono subtle">proto</span><span>优秀突破后轻仓探测，验证是否提高早期参与收益。</span></li>
            <li><span className="mono subtle">confirmed</span><span>等待回踩确认，验证是否降低失败率和回撤。</span></li>
            <li><span className="mono subtle">delta</span><span>报告必须量化等待确认的收益、回撤、胜率和样本损失。</span></li>
          </ul>
        </Panel>

        <Panel action={<Status>slices</Status>} title="稳健性切片">
          <div className="decision-chain robustness-chain">
            <div className="chain-step"><strong>年份</strong><span>避免总样本掩盖失效阶段</span></div>
            <div className="chain-step"><strong>市场状态</strong><span>risk_on / neutral / risk_off</span></div>
            <div className="chain-step"><strong>主题贡献</strong><span>避免单一热点主导结论</span></div>
          </div>
        </Panel>
      </section>
    </AppShell>
  );
}

