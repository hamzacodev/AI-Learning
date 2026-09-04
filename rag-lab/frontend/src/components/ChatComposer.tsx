"use client";

import { useRef, type FormEvent, type KeyboardEvent } from "react";

interface ChatComposerProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  onCancel: () => void;
  isPending: boolean;
}

export default function ChatComposer({
  value,
  onChange,
  onSubmit,
  onCancel,
  isPending,
}: ChatComposerProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const canSend = value.trim().length > 0 && !isPending;

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (canSend) onSubmit();
  }

  /* Enter sends, Shift plus Enter inserts a newline. */
  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      if (canSend) onSubmit();
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="flex items-end gap-3 rounded-xl border border-border bg-bg-panel p-2.5"
    >
      <label htmlFor="question" className="sr-only">
        Question
      </label>
      <textarea
        id="question"
        ref={textareaRef}
        rows={1}
        value={value}
        disabled={isPending}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask something about the Nexara knowledge base"
        className="max-h-40 min-h-[2.5rem] flex-1 resize-none bg-transparent px-2 py-2 text-sm text-text-primary placeholder:text-text-secondary focus:outline-none disabled:opacity-60"
      />

      {isPending ? (
        <button
          type="button"
          onClick={onCancel}
          className="shrink-0 rounded-lg border border-border bg-bg-panel-raised px-4 py-2 text-sm font-medium text-text-secondary transition-colors hover:text-text-primary"
        >
          Cancel
        </button>
      ) : (
        <button
          type="submit"
          disabled={!canSend}
          className="shrink-0 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-bg transition-colors hover:bg-accent-hover disabled:cursor-not-allowed disabled:opacity-40"
        >
          Send
        </button>
      )}
    </form>
  );
}
