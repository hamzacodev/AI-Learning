import type { Source } from "@/lib/api";

/** Shows the file name rather than the full path, which is long and repetitive. */
function fileName(path: string): string {
  const parts = path.split(/[\\/]/);
  return parts[parts.length - 1] || path;
}

export default function SourceChip({ source }: { source: Source }) {
  return (
    <span
      title={source.source}
      className="inline-flex items-center gap-1.5 rounded-full border border-border bg-bg-panel-raised px-2.5 py-1 text-xs text-text-secondary"
    >
      <span
        aria-hidden
        className="h-1.5 w-1.5 shrink-0 rounded-full bg-accent"
      />
      <span className="text-text-primary">{fileName(source.source)}</span>
      <span className="text-text-secondary">{source.doc_type}</span>
    </span>
  );
}
