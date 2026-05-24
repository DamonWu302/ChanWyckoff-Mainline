"use client";

import type { CSSProperties } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button, ButtonLink } from "@/components/ui/Button";
import { MiniChart, StructureChart } from "@/components/ui/Charts";
import { Metric } from "@/components/ui/Metric";
import { Panel } from "@/components/ui/Panel";
import { Status } from "@/components/ui/Status";
import { Tabs } from "@/components/ui/Tabs";

const swatches = [
  ["--bg", "var(--bg)", "var(--fg)"],
  ["--surface", "var(--surface)", "var(--fg)"],
  ["--surface-2", "var(--surface-2)", "var(--fg)"],
  ["--fg", "var(--fg)", "white"],
  ["--muted", "var(--muted)", "white"],
  ["--accent", "var(--accent)", "white"],
  ["--accent-2", "var(--accent-2)", "white"],
  ["--warn", "var(--warn)", "var(--fg)"],
  ["--danger", "var(--danger)", "white"],
  ["--info", "var(--info)", "white"],
];

export function DesignSystemPreview() {
  return (
    <AppShell note="设计系统预览页仅用于开发环境，验证 temp 原型样式在 Next.js 组件体系中的还原质量。">
      <PageHeader
        actions={<Status variant="info">dev only</Status>}
        eyebrow="Design System"
        lead="用于检查颜色、字体、按钮、卡片、表单、布局、表格、图表与交互状态是否与原生 HTML 原型保持一致。"
        title="设计系统预览"
      />

      <section className="grid cols-2 section-gap">
        <Panel action={<Status>tokens</Status>} title="颜色变量">
          <div className="design-swatch-grid">
            {swatches.map(([name, color, fg]) => (
              <div className="design-swatch" key={name} style={{ "--swatch": color, "--swatch-fg": fg } as CSSProperties}>
                <strong className="mono">{name}</strong>
                <span className="mono subtle">{color}</span>
              </div>
            ))}
          </div>
        </Panel>

        <Panel action={<Status>type</Status>} title="字体层级">
          <div className="design-scale">
            <span className="mono subtle">h1 / display</span>
            <h1>今日作战台</h1>
          </div>
          <div className="design-scale">
            <span className="mono subtle">h2 / panel</span>
            <h2>趋势容量核心排序</h2>
          </div>
          <div className="design-scale">
            <span className="mono subtle">body</span>
            <span>先看大盘是否允许进攻，再看穿越主线与核心票。</span>
          </div>
          <div className="design-scale">
            <span className="mono subtle">mono</span>
            <span className="mono">risk_on {"->"} confirmed_3buy {"->"} risk cap</span>
          </div>
        </Panel>
      </section>

      <section className="grid cols-3 section-gap">
        <Metric foot="进攻仓位需等待主线与结构共振" label="Market regime" value="neutral" />
        <Metric foot="confirmed 1 / emerging 2" label="Active mainlines" value="3" />
        <Metric foot="neutral 下总仓位上限示例" label="Exposure gate" value="≤ 45%" />
      </section>

      <section className="grid cols-2 section-gap">
        <Panel action={<Status>buttons</Status>} title="按钮与状态">
          <div className="stack">
            <div className="component-row">
              <Button>默认按钮</Button>
              <Button variant="primary">主按钮</Button>
              <Button variant="ghost">幽灵按钮</Button>
              <ButtonLink href="/today-operations" variant="primary">页面链接</ButtonLink>
            </div>
            <div className="component-row">
              <Status>default</Status>
              <Status variant="good">confirmed_mainline</Status>
              <Status variant="info">proto_3buy</Status>
              <Status variant="warn">neutral</Status>
              <Status variant="danger">failed_3buy</Status>
            </div>
          </div>
        </Panel>

        <Panel action={<Status>forms</Status>} title="表单控件">
          <div className="stack">
            <div className="field">
              <label htmlFor="previewSelect">状态筛选</label>
              <select id="previewSelect" defaultValue="confirmed_3buy">
                <option value="proto_3buy">proto_3buy</option>
                <option value="confirmed_3buy">confirmed_3buy</option>
                <option value="failed_3buy">failed_3buy</option>
              </select>
            </div>
            <div className="field">
              <label htmlFor="previewInput">分数阈值</label>
              <input id="previewInput" defaultValue="80" />
            </div>
            <div className="field">
              <label htmlFor="previewText">复盘备注</label>
              <textarea id="previewText" defaultValue="回踩缩量，仍在容忍区上方。" />
            </div>
          </div>
        </Panel>
      </section>

      <section className="grid cols-2 section-gap">
        <Panel action={<Status>tabs</Status>} title="标签页">
          <Tabs
            items={[
              { id: "theme", label: "题材状态", panel: <div className="empty">题材状态面板</div> },
              { id: "rank", label: "核心排序", panel: <div className="empty">核心排序面板</div> },
            ]}
          />
        </Panel>

        <Panel action={<Status>table</Status>} bodyClassName="table-panel-body" title="表格">
          <div className="table-wrap">
            <table>
              <thead><tr><th>股票</th><th>主线</th><th>状态</th><th>分数</th></tr></thead>
              <tbody>
                <tr><td><strong>机器人核心 Alpha</strong></td><td><Status variant="good">机器人</Status></td><td><Status variant="good">confirmed_3buy</Status></td><td className="mono">86</td></tr>
                <tr><td><strong>CPO 核心 Beta</strong></td><td><Status variant="info">CPO</Status></td><td><Status variant="info">proto_3buy</Status></td><td className="mono">78</td></tr>
              </tbody>
            </table>
          </div>
        </Panel>
      </section>

      <section className="grid detail">
        <Panel action={<Status>chart</Status>} title="迷你图">
          <MiniChart />
        </Panel>
        <Panel action={<Status variant="good">structure</Status>} title="结构图">
          <StructureChart />
        </Panel>
      </section>
    </AppShell>
  );
}
