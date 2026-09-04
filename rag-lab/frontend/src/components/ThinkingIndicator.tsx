/**
 * Shown while an answer is generating. The elapsed counter matters here
 * because the backend routinely takes 30 to 60 seconds per question.
 */
export default function ThinkingIndicator({ seconds }: { seconds: number }) {
  return (
    <div className="flex items-center gap-3 rounded-2xl rounded-bl-md border border-border bg-bg-panel px-4 py-3">
      <span className="flex gap-1" aria-hidden>
        {[0, 1, 2].map((index) => (
          <span
            key={index}
            className="h-1.5 w-1.5 rounded-full bg-accent"
            style={{
              animation: "pulse-dot 1.2s ease-in-out infinite",
              animationDelay: `${index * 0.18}s`,
            }}
          />
        ))}
      </span>
      <span className="text-sm text-text-secondary">
        Retrieving and generating, {seconds}s
      </span>
    </div>
  );
}
