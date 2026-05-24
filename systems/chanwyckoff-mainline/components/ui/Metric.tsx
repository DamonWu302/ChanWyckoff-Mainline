type MetricProps = {
  label: string;
  value: string;
  foot: string;
};

export function Metric({ label, value, foot }: MetricProps) {
  return (
    <div className="metric">
      <span className="metric-label">{label}</span>
      <span className="metric-value">{value}</span>
      <span className="metric-foot">{foot}</span>
    </div>
  );
}

