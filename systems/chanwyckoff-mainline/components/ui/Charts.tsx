import type { CSSProperties } from "react";
import { cn } from "@/lib/cn";

type ChartProps = {
  className?: string;
  lineStyle?: string;
};

export function MiniChart({ className, lineStyle }: ChartProps) {
  return (
    <div className={cn("chart", className)}>
      <div className="chart-line" style={lineStyle ? { clipPath: lineStyle } : undefined} />
    </div>
  );
}

export function StructureChart() {
  const candles = [
    ["130px", "oklch(42% 0.03 240)"],
    ["112px", "oklch(42% 0.03 240)"],
    ["148px", "oklch(42% 0.03 240)"],
    ["96px", "oklch(42% 0.03 240)"],
    ["138px", "oklch(42% 0.03 240)"],
    ["122px", "oklch(42% 0.03 240)"],
    ["156px", "oklch(42% 0.03 240)"],
    ["146px", "oklch(42% 0.03 240)"],
    ["181px", "var(--accent)"],
    ["214px", "var(--accent)"],
    ["188px", "var(--accent)"],
    ["168px", "oklch(62% 0.11 145)"],
    ["174px", "oklch(62% 0.11 145)"],
    ["210px", "var(--accent)"],
  ];

  return (
    <div aria-label="30 分钟结构示意图" className="structure-chart">
      <div className="target-line" />
      <div className="pullback-zone" />
      <div className="breakout-line" />
      <div className="range-band" />
      <div className="stop-band" />
      <div className="candles">
        {candles.map(([height, color], index) => (
          <span
            className="candle"
            key={`${height}-${index}`}
            style={{ "--h": height, "--c": color } as CSSProperties}
          />
        ))}
      </div>
      <span className="caption target">目标/前高/测量位</span>
      <span className="caption breakout">中枢上沿突破</span>
      <span className="caption center">工程中枢 / 平台区</span>
      <span className="caption stop">结构失败止损区</span>
    </div>
  );
}
