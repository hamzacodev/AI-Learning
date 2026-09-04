import { STATUS_COLOR, STATUS_LABEL, type Status } from "@/lib/metrics";

interface MetricCardProps {
  label: string;
  /** Preformatted headline number, for example "0.73" or "86%". */
  value: string;
  /** Unit shown next to the value, for example "/ 5". */
  suffix?: string;
  status: Status;
  /** Position of the value on its own scale, 0 to 1, drives the meter width. */
  fill: number;
  hint: string;
}

export default function MetricCard({
  label,
  value,
  suffix,
  status,
  fill,
  hint,
}: MetricCardProps) {
  const color = STATUS_COLOR[status];
  const width = `${Math.max(0, Math.min(1, fill)) * 100}%`;

  return (
    <div className="rounded-xl border border-border bg-bg-panel p-4">
      <div className="flex items-baseline justify-between gap-2">
        <p className="text-xs font-medium tracking-wide text-text-secondary uppercase">
          {label}
        </p>
        <span className="text-xs font-medium" style={{ color }}>
          {STATUS_LABEL[status]}
        </span>
      </div>

      <p className="mt-3 font-heading text-3xl font-semibold text-text-primary tabular-nums">
        {value}
        {suffix && (
          <span className="ml-1 text-base font-medium text-text-secondary">
            {suffix}
          </span>
        )}
      </p>

      <div
        className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-bg-panel-raised"
        role="presentation"
      >
        <div
          className="h-full rounded-full transition-[width] duration-500"
          style={{ width, backgroundColor: color }}
        />
      </div>

      <p className="mt-2 text-xs text-text-secondary">{hint}</p>
    </div>
  );
}
