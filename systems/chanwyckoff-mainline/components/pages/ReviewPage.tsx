"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button, ButtonLink } from "@/components/ui/Button";
import { Panel } from "@/components/ui/Panel";
import { Status } from "@/components/ui/Status";
import {
  fallbackReviewFailureStats,
  fetchReviewFailureStats,
  type ReviewFailureStats,
} from "@/lib/reviewStats";

type ReviewEvent = {
  time: string;
  state: string;
  note: string;
  status: string;
  variant: "default" | "good" | "info" | "warn" | "danger";
};

const initialEvents: ReviewEvent[] = [
  {
    time: "T+0 14:00",
    state: "prepared",
    note: "回踩缩量，仍在容忍区上方；等待真实操作价映射。",
    status: "规则一致",
    variant: "good",
  },
  {
    time: "T+0 10:30",
    state: "proto_3buy",
    note: "突破后进入轻仓观察队列，未由 LLM 改写信号。",
    status: "系统",
    variant: "info",
  },
];

function sortedDistribution(items: Record<string, number>) {
  return Object.entries(items).sort((left, right) => right[1] - left[1] || left[0].localeCompare(right[0]));
}

export function ReviewPage() {
  const [events, setEvents] = useState(initialEvents);
  const [failureStats, setFailureStats] = useState<ReviewFailureStats>(fallbackReviewFailureStats);
  const [manualState, setManualState] = useState("prepared");
  const [failureReason, setFailureReason] = useState("未失败");
  const [note, setNote] = useState("");
  const manualDistribution = useMemo(
    () => sortedDistribution(failureStats.manual_failure_reasons),
    [failureStats.manual_failure_reasons],
  );
  const llmDistribution = useMemo(
    () => sortedDistribution(failureStats.llm_failure_types),
    [failureStats.llm_failure_types],
  );

  useEffect(() => {
    let mounted = true;
    fetchReviewFailureStats()
      .then((stats) => {
        if (mounted) setFailureStats(stats);
      })
      .catch(() => {
        if (mounted) setFailureStats(fallbackReviewFailureStats);
      });
    return () => {
      mounted = false;
    };
  }, []);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setEvents((current) => [
      {
        time: "刚刚",
        state: manualState,
        note: note.trim() || "未填写人工备注",
        status: failureReason,
        variant: failureReason === "未失败" ? "good" : "warn",
      },
      ...current,
    ]);
    setManualState("prepared");
    setFailureReason("未失败");
    setNote("");
  }

  return (
    <AppShell note="人工确认状态不会改写规则信号；它只记录交易计划、执行结果和失败归因。">
      <PageHeader
        actions={<ButtonLink href="/today-operations">回作战台</ButtonLink>}
        eyebrow="Review Loop"
        lead="复盘页保留候选从 prepared、bought、skipped 到 sold 的人工轨迹，并把失败样本分类回流给规则改进。"
        title="规则输出与人工复盘"
      />

      <section className="grid detail">
        <Panel action={<Status variant="good">机器人核心 Alpha</Status>} bodyClassName="stack" title="当前信号记录">
          <div className="decision-chain review-chain">
            <div className="chain-step"><strong>规则状态</strong><span>confirmed_3buy / wyckoff 86</span></div>
            <div className="chain-step"><strong>人工状态</strong><span>prepared，等待执行价确认</span></div>
            <div className="chain-step"><strong>风控</strong><span>结构失败止损 + 时间止损</span></div>
            <div className="chain-step"><strong>复盘目标</strong><span>验证确认是否提升质量</span></div>
          </div>
          <div className="timeline">
            {events.map((item, index) => (
              <div className="event" key={`${item.time}-${item.state}-${index}`}>
                <span className="mono">{item.time}</span>
                <div>
                  <strong>{item.state}</strong>
                  <div className="subtle">{item.note}</div>
                </div>
                <Status variant={item.variant}>{item.status}</Status>
              </div>
            ))}
          </div>
        </Panel>

        <Panel action={<Status>manual</Status>} title="新增复盘备注">
          <form className="stack" onSubmit={handleSubmit}>
            <div className="field">
              <label htmlFor="manualState">人工状态</label>
              <select id="manualState" onChange={(event) => setManualState(event.target.value)} required value={manualState}>
                <option value="prepared">prepared</option>
                <option value="bought">bought</option>
                <option value="skipped">skipped</option>
                <option value="sold">sold</option>
              </select>
            </div>
            <div className="field">
              <label htmlFor="failureReason">失败/观察归因</label>
              <select id="failureReason" onChange={(event) => setFailureReason(event.target.value)} value={failureReason}>
                <option value="未失败">未失败</option>
                <option value="供应重入">供应重入</option>
                <option value="跌回中枢">跌回中枢</option>
                <option value="时间止损">时间止损</option>
                <option value="题材退潮">题材退潮</option>
              </select>
            </div>
            <div className="field">
              <label htmlFor="note">人工备注</label>
              <textarea
                id="note"
                onChange={(event) => setNote(event.target.value)}
                placeholder="记录盘中观察、执行价差、跳过原因或后续复盘问题"
                value={note}
              />
            </div>
            <Button type="submit" variant="primary">加入复盘记录</Button>
          </form>
        </Panel>
      </section>

      <section className="grid cols-2 section-gap">
        <Panel
          action={<Status variant={failureStats.total_failed_records > 0 ? "warn" : "good"}>{failureStats.total_failed_records}</Status>}
          title="失败原因分布"
        >
          <div className="timeline compact">
            {manualDistribution.map(([reason, count]) => (
              <div className="event" key={reason}>
                <span className="mono">{count}</span>
                <div>
                  <strong>{reason}</strong>
                  <div className="subtle">人工复盘归因</div>
                </div>
                <Status variant="warn">manual</Status>
              </div>
            ))}
          </div>
        </Panel>

        <Panel action={<Status variant="info">LLM</Status>} title="LLM 失败样本总结">
          <div className="timeline compact">
            {llmDistribution.map(([reason, count]) => (
              <div className="event" key={reason}>
                <span className="mono">{count}</span>
                <div>
                  <strong>{reason}</strong>
                  <div className="subtle">只作为解释，不改变规则结果</div>
                </div>
                <Status variant="info">summary</Status>
              </div>
            ))}
          </div>
        </Panel>
      </section>
    </AppShell>
  );
}
