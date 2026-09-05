"use client";

import { useEffect, useRef, useState } from "react";

import AppHeader from "@/components/AppHeader";
import ChatComposer from "@/components/ChatComposer";
import ChatMessage, { type ChatMessageData } from "@/components/ChatMessage";
import ThinkingIndicator from "@/components/ThinkingIndicator";
import { askQuestion, type ChatTurn } from "@/lib/api";

const EXAMPLE_QUESTIONS = [
  "Who founded Nexara and where is it headquartered?",
  "What is the Bellmark Distribution contract worth?",
  "Which product team is Hana Kobayashi on?",
];

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessageData[]>([]);
  const [draft, setDraft] = useState("");
  const [isPending, setIsPending] = useState(false);
  const [elapsed, setElapsed] = useState(0);

  const controllerRef = useRef<AbortController | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  /* Answers take 30 to 60 seconds, so the wait gets a visible counter. */
  useEffect(() => {
    if (!isPending) {
      setElapsed(0);
      return;
    }
    const startedAt = Date.now();
    const timer = setInterval(() => {
      setElapsed(Math.floor((Date.now() - startedAt) / 1000));
    }, 1000);
    return () => clearInterval(timer);
  }, [isPending]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, isPending]);

  /* Drop any in flight request if the page goes away. */
  useEffect(() => () => controllerRef.current?.abort(), []);

  function appendMessage(message: ChatMessageData) {
    setMessages((current) => [...current, message]);
  }

  async function send(question: string) {
    const trimmed = question.trim();
    if (!trimmed || isPending) return;

    /*
      The conversation as it stands before this question. `messages` still
      holds the pre-append list here, since the new turn goes in through a
      functional update below, so the question is not duplicated into its own
      history. Error bubbles are UI artifacts rather than real assistant
      replies, so they are left out, and only role and content are sent.
    */
    const history: ChatTurn[] = messages
      .filter((message) => !message.isError)
      .map(({ role, content }) => ({ role, content }));

    appendMessage({
      id: crypto.randomUUID(),
      role: "user",
      content: trimmed,
    });
    setDraft("");
    setIsPending(true);

    const controller = new AbortController();
    controllerRef.current = controller;

    try {
      const result = await askQuestion(trimmed, history, controller.signal);
      appendMessage({
        id: crypto.randomUUID(),
        role: "assistant",
        content: result.answer || "The backend returned an empty answer.",
        sources: result.sources,
      });
    } catch (error) {
      if (controller.signal.aborted) {
        appendMessage({
          id: crypto.randomUUID(),
          role: "assistant",
          content: "Request cancelled.",
          isError: true,
        });
      } else {
        appendMessage({
          id: crypto.randomUUID(),
          role: "assistant",
          content:
            error instanceof Error
              ? error.message
              : "Something went wrong while asking the backend.",
          isError: true,
        });
      }
    } finally {
      controllerRef.current = null;
      setIsPending(false);
    }
  }

  const isEmpty = messages.length === 0 && !isPending;

  return (
    <div className="flex h-dvh flex-col">
      <AppHeader
        title="Nexara RAG"
        linkHref="/dashboard"
        linkLabel="Dashboard"
      />

      <main className="flex-1 overflow-y-auto">
        <div className="mx-auto w-full max-w-5xl px-5 py-6">
          {isEmpty ? (
            <div className="mt-10">
              <h2 className="text-lg font-semibold text-text-primary">
                Ask the knowledge base
              </h2>
              <p className="mt-2 max-w-xl text-sm leading-relaxed text-text-secondary">
                Questions are answered from the indexed Nexara documents only.
                Each answer lists the files it was built from. Responses
                typically take 30 to 60 seconds.
              </p>

              <ul className="mt-6 flex flex-col gap-2">
                {EXAMPLE_QUESTIONS.map((example) => (
                  <li key={example}>
                    <button
                      type="button"
                      onClick={() => send(example)}
                      className="w-full rounded-lg border border-border bg-bg-panel px-4 py-3 text-left text-sm text-text-secondary transition-colors hover:border-accent hover:text-text-primary"
                    >
                      {example}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <div className="flex flex-col gap-5">
              {messages.map((message) => (
                <ChatMessage key={message.id} message={message} />
              ))}

              {isPending && (
                <div className="flex items-start">
                  <ThinkingIndicator seconds={elapsed} />
                </div>
              )}
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      </main>

      <div className="border-t border-border bg-bg">
        <div className="mx-auto w-full max-w-5xl px-5 py-4">
          <ChatComposer
            value={draft}
            onChange={setDraft}
            onSubmit={() => send(draft)}
            onCancel={() => controllerRef.current?.abort()}
            isPending={isPending}
          />
          <p className="mt-2 px-1 text-xs text-text-secondary">
            Press Enter to send, Shift plus Enter for a new line.
          </p>
        </div>
      </div>
    </div>
  );
}
