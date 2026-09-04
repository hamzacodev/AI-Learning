"use client";

import { useEffect, useState } from "react";

/** "2 minutes ago" style formatting, coarse on purpose. */
function relative(from: Date, now: Date): string {
  const seconds = Math.round((now.getTime() - from.getTime()) / 1000);

  if (seconds < 5) return "just now";
  if (seconds < 60) return `${seconds} seconds ago`;

  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes} ${minutes === 1 ? "minute" : "minutes"} ago`;

  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} ${hours === 1 ? "hour" : "hours"} ago`;

  const days = Math.floor(hours / 24);
  if (days < 30) return `${days} ${days === 1 ? "day" : "days"} ago`;

  return from.toLocaleDateString();
}

export default function RelativeTime({ timestamp }: { timestamp: string }) {
  /*
    Rendered only after mount. The server and the browser would otherwise
    compute "now" at different moments and disagree, which React reports as
    a hydration mismatch.
  */
  const [label, setLabel] = useState<string | null>(null);

  useEffect(() => {
    const parsed = new Date(timestamp);
    if (Number.isNaN(parsed.getTime())) {
      setLabel(null);
      return;
    }

    const update = () => setLabel(relative(parsed, new Date()));
    update();

    const timer = setInterval(update, 30_000);
    return () => clearInterval(timer);
  }, [timestamp]);

  const parsed = new Date(timestamp);
  if (Number.isNaN(parsed.getTime())) return null;

  return (
    <time
      dateTime={timestamp}
      title={parsed.toLocaleString()}
      className="shrink-0 text-xs text-text-secondary tabular-nums"
      suppressHydrationWarning
    >
      {label ?? ""}
    </time>
  );
}
