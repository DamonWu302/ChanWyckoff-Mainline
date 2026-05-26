"use client";

import type { CSSProperties } from "react";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { PageHeader } from "@/components/layout/PageHeader";
import { ButtonLink } from "@/components/ui/Button";
import { StructureChart } from "@/components/ui/Charts";
import { Panel } from "@/components/ui/Panel";
import { Status } from "@/components/ui/Status";
import { fallbackSignalDetail, fetchSignalDetail } from "@/lib/signalDetail";

export function SignalDetailPage() {
  const [detail, setDetail] = useState(fallbackSignalDetail);

  useEffect(() => {
    let mounted = true;
    fetchSignalDetail()
      .then((nextDetail) => {
        if (mounted) setDetail(nextDetail);
      })
      .catch(() => {
        if (mounted) setDetail(fallbackSignalDetail);
      });
    return () => {
      mounted = false;
    };
  }, []);

  return (
    <AppShell note="展示价格时区分前复权分析价与真实操作价，避免除权结构和执行报价混淆。">
      <PageHeader
        actions={
          <>
            <Status variant="warn">market neutral</Status>
            <Status variant="good">wyckoff {detail.wyckoff.score}</Status>
            <ButtonLink href="/review" variant="primary">记录人工状态</ButtonLink>
          </>
        }
        eyebrow="Signal Detail"
        lead="这页把 30 分钟平台/中枢、突破、回踩、止损、目标和威科夫证据放到同一个解释面板里，帮助用户判断为什么它进入候选池。"
        title={`${detail.name} · ${detail.state}`}
      />

      <section className="grid detail">
        <Panel action={<Status variant="good">{detail.state}</Status>} title="30 分钟结构图">
          <StructureChart />
        </Panel>

        <div className="stack">
          <Panel action={<Status variant="good">valid</Status>} title="信号状态机">
            <ul className="rule-list">
              <li><span className="mono subtle">structure</span><span>{detail.structure.label} / 上沿 {detail.structure.upper} / 下沿 {detail.structure.lower}</span></li>
              <li><span className="mono subtle">breakout</span><span>收盘 {detail.price_volume.breakout_close}，强度 {detail.price_volume.breakout_strength}，量比 {detail.price_volume.breakout_volume_ratio}</span></li>
              <li><span className="mono subtle">pullback</span><span>{detail.price_volume.pullback_volume} / {detail.price_volume.support_quality}</span></li>
            </ul>
          </Panel>

          <Panel action={<Status variant="good">{detail.wyckoff.score}</Status>} title="威科夫评分">
            <div className="split">
              <div className="score-ring" style={{ "--score": `${detail.wyckoff.score}%` } as CSSProperties}>{detail.wyckoff.score}</div>
              <ul className="rule-list signal-score-list">
                <li><span className="mono subtle">背景</span><span>{detail.wyckoff.background}</span></li>
                <li><span className="mono subtle">特征</span><span>{detail.wyckoff.features.join(" / ")}</span></li>
                <li><span className="mono subtle">预判</span><span>{detail.wyckoff.forecast}</span></li>
              </ul>
            </div>
          </Panel>

          <Panel action={<Status variant="warn">bounded</Status>} title="仓位与风控">
            <ul className="rule-list">
              <li><span className="mono subtle">position</span><span>{detail.suggested_action} / 建议 {detail.risk.position_pct}%</span></li>
              <li><span className="mono subtle">exit</span><span>止损 {detail.risk.stop_loss} / 目标 {detail.risk.target_price} / 时间止损 {detail.risk.time_stop_bars} 根 30m</span></li>
              <li><span className="mono subtle">invalid</span><span>{detail.risk.invalidations.join(" / ")}</span></li>
            </ul>
          </Panel>
        </div>
      </section>
    </AppShell>
  );
}
