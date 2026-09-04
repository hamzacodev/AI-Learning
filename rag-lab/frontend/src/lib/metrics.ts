import type { AnswerResult, RetrievalResult } from "@/lib/api";

/** Shared scoring vocabulary for cards and charts. */
export type Status = "good" | "fair" | "poor";

export const STATUS_COLOR: Record<Status, string> = {
  good: "var(--color-green)",
  fair: "var(--color-yellow)",
  poor: "var(--color-red)",
};

export const STATUS_LABEL: Record<Status, string> = {
  good: "Good",
  fair: "Fair",
  poor: "Needs work",
};

/** For values on a 0 to 1 scale, such as MRR and keyword coverage. */
export function ratioStatus(value: number): Status {
  if (value >= 0.7) return "good";
  if (value >= 0.4) return "fair";
  return "poor";
}

/** For judge scores on a 1 to 5 scale. */
export function scoreStatus(value: number): Status {
  if (value >= 4) return "good";
  if (value >= 3) return "fair";
  return "poor";
}

export function formatRatio(value: number): string {
  return value.toFixed(2);
}

export function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

export function formatScore(value: number): string {
  return value.toFixed(2);
}

/** "direct_fact" reads as "Direct fact" in the interface. */
export function formatCategory(category: string): string {
  const spaced = category.replace(/[_-]+/g, " ").trim();
  if (!spaced) return "Uncategorized";
  return spaced.charAt(0).toUpperCase() + spaced.slice(1);
}

export interface CategoryPoint {
  category: string;
  label: string;
  value: number;
  count: number;
}

/**
 * Groups rows by their category and averages one numeric field.
 * Categories come back in the order they first appear in the results.
 */
export function averageByCategory<T extends RetrievalResult | AnswerResult>(
  rows: T[],
  pick: (row: T) => number,
): CategoryPoint[] {
  const totals = new Map<string, { sum: number; count: number }>();

  for (const row of rows) {
    const key = row.category || "uncategorized";
    const entry = totals.get(key) ?? { sum: 0, count: 0 };
    entry.sum += pick(row);
    entry.count += 1;
    totals.set(key, entry);
  }

  return Array.from(totals, ([category, { sum, count }]) => ({
    category,
    label: formatCategory(category),
    value: count > 0 ? sum / count : 0,
    count,
  }));
}
