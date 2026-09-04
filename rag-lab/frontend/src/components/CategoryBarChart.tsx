"use client";

import {
  Bar,
  BarChart,
  Cell,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import {
  STATUS_COLOR,
  type CategoryPoint,
  type Status,
} from "@/lib/metrics";

interface CategoryBarChartProps {
  title: string;
  description: string;
  data: CategoryPoint[];
  /** Upper bound of the value axis, 1 for MRR and 5 for judge scores. */
  max: number;
  statusOf: (value: number) => Status;
  formatValue: (value: number) => string;
}

interface TooltipPayloadItem {
  payload: CategoryPoint;
}

function ChartTooltip({
  active,
  payload,
  formatValue,
}: {
  active?: boolean;
  payload?: TooltipPayloadItem[];
  formatValue: (value: number) => string;
}) {
  if (!active || !payload || payload.length === 0) return null;
  const point = payload[0].payload;

  return (
    <div className="rounded-lg border border-border bg-bg-panel-raised px-3 py-2 shadow-lg">
      <p className="text-xs font-medium text-text-primary">{point.label}</p>
      <p className="mt-0.5 text-xs text-text-secondary">
        {formatValue(point.value)} across {point.count}{" "}
        {point.count === 1 ? "question" : "questions"}
      </p>
    </div>
  );
}

export default function CategoryBarChart({
  title,
  description,
  data,
  max,
  statusOf,
  formatValue,
}: CategoryBarChartProps) {
  return (
    <section className="rounded-xl border border-border bg-bg-panel p-5">
      <h2 className="text-sm font-semibold text-text-primary">{title}</h2>
      <p className="mt-1 text-xs text-text-secondary">{description}</p>

      <div className="mt-5 h-64 w-full">
        {data.length === 0 ? (
          <div className="flex h-full items-center justify-center text-sm text-text-secondary">
            No category data in this run.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={data}
              margin={{ top: 4, right: 8, bottom: 4, left: -16 }}
            >
              <CartesianGrid
                vertical={false}
                stroke="var(--color-border)"
                strokeDasharray="3 3"
              />
              <XAxis
                dataKey="label"
                tickLine={false}
                axisLine={{ stroke: "var(--color-border)" }}
                tick={{ fill: "var(--color-text-secondary)", fontSize: 11 }}
                interval={0}
              />
              <YAxis
                domain={[0, max]}
                tickLine={false}
                axisLine={false}
                tick={{ fill: "var(--color-text-secondary)", fontSize: 11 }}
                width={44}
              />
              <Tooltip
                cursor={{ fill: "var(--color-bg-panel-raised)" }}
                content={<ChartTooltip formatValue={formatValue} />}
              />
              <Bar dataKey="value" radius={[4, 4, 0, 0]} maxBarSize={56}>
                {data.map((point) => (
                  <Cell
                    key={point.category}
                    fill={STATUS_COLOR[statusOf(point.value)]}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </section>
  );
}
