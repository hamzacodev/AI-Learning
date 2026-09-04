import SourceChip from "@/components/SourceChip";
import type { Source } from "@/lib/api";

export type ChatRole = "user" | "assistant";

export interface ChatMessageData {
  id: string;
  role: ChatRole;
  content: string;
  sources?: Source[];
  /** Set when the request failed, so the bubble can be styled as a problem. */
  isError?: boolean;
}

/** The same file often backs several retrieved chunks, so collapse repeats. */
function uniqueSources(sources: Source[]): Source[] {
  const seen = new Set<string>();
  return sources.filter((source) => {
    if (seen.has(source.source)) return false;
    seen.add(source.source);
    return true;
  });
}

export default function ChatMessage({ message }: { message: ChatMessageData }) {
  const isUser = message.role === "user";
  const sources = message.sources ? uniqueSources(message.sources) : [];

  return (
    <div className={`flex flex-col ${isUser ? "items-end" : "items-start"}`}>
      <div
        className={[
          "max-w-[85ch] rounded-2xl border px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap",
          isUser
            ? "rounded-br-md border-accent/40 bg-bg-user text-text-primary"
            : "rounded-bl-md border-border bg-bg-panel text-text-primary",
          message.isError ? "border-red/50 text-red" : "",
        ].join(" ")}
      >
        {message.content}
      </div>

      {sources.length > 0 && (
        <div className="mt-2 flex max-w-[85ch] flex-wrap gap-1.5">
          {sources.map((source) => (
            <SourceChip key={source.source} source={source} />
          ))}
        </div>
      )}
    </div>
  );
}
