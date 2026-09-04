import RelativeTime from "@/components/RelativeTime";
import SourceChip from "@/components/SourceChip";
import type { ChatLogEntry, Source } from "@/lib/api";

const PREVIEW_LENGTH = 100;

/** Trim on a word boundary so the preview does not cut mid word. */
function preview(answer: string): string {
  const flat = answer.replace(/\s+/g, " ").trim();
  if (flat.length <= PREVIEW_LENGTH) return flat;

  const cut = flat.slice(0, PREVIEW_LENGTH);
  const lastSpace = cut.lastIndexOf(" ");
  return `${(lastSpace > 40 ? cut.slice(0, lastSpace) : cut).trimEnd()}...`;
}

/** One file can back several retrieved chunks, so collapse repeats. */
function uniqueSources(sources: Source[]): Source[] {
  const seen = new Set<string>();
  return sources.filter((entry) => {
    if (seen.has(entry.source)) return false;
    seen.add(entry.source);
    return true;
  });
}

export default function ActivityRow({ entry }: { entry: ChatLogEntry }) {
  const sources = uniqueSources(entry.sources);

  return (
    <li className="border-b border-border px-4 py-3.5 last:border-b-0">
      <div className="flex items-baseline justify-between gap-4">
        <p className="text-sm font-medium text-text-primary">
          {entry.question}
        </p>
        <RelativeTime timestamp={entry.timestamp} />
      </div>

      <p className="mt-1.5 text-sm leading-relaxed text-text-secondary">
        {preview(entry.answer)}
      </p>

      {sources.length > 0 && (
        <div className="mt-2.5 flex flex-wrap gap-1.5">
          {sources.map((source) => (
            <SourceChip key={source.source} source={source} />
          ))}
        </div>
      )}
    </li>
  );
}
