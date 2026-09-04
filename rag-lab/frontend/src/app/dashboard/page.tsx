"use client";

import { useCallback, useEffect, useState } from "react";

import ActivityRow from "@/components/ActivityRow";
import AppHeader from "@/components/AppHeader";
import CategoryBarChart from "@/components/CategoryBarChart";
import EmptyState from "@/components/EmptyState";
import MetricCard from "@/components/MetricCard";
import {
  fetchChatLog,
  fetchEvalResults,
  type ChatLogEntry,
  type EvalResults,
} from "@/lib/api";
import {
  averageByCategory,
  formatPercent,
  formatRatio,
  formatScore,
  ratioStatus,
  scoreStatus,
} from "@/lib/metrics";

type LoadState = "loading" | "ready" | "error";

export default function DashboardPage() {
  const [state, setState] = useState<LoadState>("loading");
  const [results, setResults] = useState<EvalResults | null>(null);
  const [errorMessage, setErrorMessage] = useState("");

  /* Live chat activity is loaded separately, so a failure in one does not
     blank out the other. */
  const [activity, setActivity] = useState<ChatLogEntry[]>([]);
  const [activityState, setActivityState] = useState<LoadState>("loading");

  const load = useCallback(async (signal?: AbortSignal) => {
    setState("loading");
    try {
      const data = await fetchEvalResults(signal);
      if (signal?.aborted) return;
      setResults(data);
      setState("ready");
    } catch (error) {
      if (signal?.aborted) return;
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Could not load evaluation results.",
      );
      setState("error");
    }
  }, []);

  const loadActivity = useCallback(async (signal?: AbortSignal) => {
    setActivityState("loading");
    try {
      const entries = await fetchChatLog(signal);
      if (signal?.aborted) return;
      setActivity(entries);
      setActivityState("ready");
    } catch {
      if (signal?.aborted) return;
      setActivityState("error");
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    void load(controller.signal);
    void loadActivity(controller.signal);
    return () => controller.abort();
  }, [load, loadActivity]);

  const summary = results?.summary;
  const mrrByCategory = averageByCategory(results?.retrieval ?? [], (row) => row.mrr);
  const accuracyByCategory = averageByCategory(
    results?.answers ?? [],
    (row) => row.accuracy,
  );
  const questionCount = Math.max(
    results?.retrieval.length ?? 0,
    results?.answers.length ?? 0,
  );

  return (
    <div className="min-h-dvh">
      <AppHeader title="Nexara RAG" linkHref="/" linkLabel="Chat" />

      <main className="mx-auto w-full max-w-5xl px-5 py-8">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <h2 className="font-heading text-2xl font-semibold text-text-primary">
              RAG Evaluation Dashboard
            </h2>
            <p className="mt-1.5 text-sm text-text-secondary">
              {state === "ready" && results
                ? `Retrieval and answer quality across ${questionCount} test ${
                    questionCount === 1 ? "question" : "questions"
                  }.`
                : "Retrieval and answer quality from the most recent evaluation run."}
            </p>
          </div>

          <button
            type="button"
            onClick={() => {
              void load();
              void loadActivity();
            }}
            disabled={state === "loading"}
            className="rounded-lg border border-border bg-bg-panel px-3.5 py-2 text-sm font-medium text-text-secondary transition-colors hover:border-accent hover:text-text-primary disabled:cursor-not-allowed disabled:opacity-50"
          >
            {state === "loading" ? "Loading" : "Refresh"}
          </button>
        </div>

        <div className="mt-7">
          {state === "loading" && <LoadingSkeleton />}

          {state === "error" && (
            <EmptyState
              title="Could not load results"
              description={errorMessage}
            >
              <button
                type="button"
                onClick={() => void load()}
                className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-bg transition-colors hover:bg-accent-hover"
              >
                Try again
              </button>
            </EmptyState>
          )}

          {state === "ready" && !summary && (
            <EmptyState
              title="No evaluation results yet"
              description="Run the evaluation on the backend, then refresh this page. Results appear here once the run finishes."
            />
          )}

          {state === "ready" && summary && (
            <div className="flex flex-col gap-6">
              <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-5">
                <MetricCard
                  label="MRR"
                  value={formatRatio(summary.mrr)}
                  status={ratioStatus(summary.mrr)}
                  fill={summary.mrr}
                  hint="Rank of the first chunk holding each keyword."
                />
                <MetricCard
                  label="Keyword coverage"
                  value={formatPercent(summary.keyword_coverage)}
                  status={ratioStatus(summary.keyword_coverage)}
                  fill={summary.keyword_coverage}
                  hint="Expected keywords found anywhere in retrieval."
                />
                <MetricCard
                  label="Accuracy"
                  value={formatScore(summary.accuracy)}
                  suffix="/ 5"
                  status={scoreStatus(summary.accuracy)}
                  fill={summary.accuracy / 5}
                  hint="Factual match against the reference answer."
                />
                <MetricCard
                  label="Completeness"
                  value={formatScore(summary.completeness)}
                  suffix="/ 5"
                  status={scoreStatus(summary.completeness)}
                  fill={summary.completeness / 5}
                  hint="How much of the reference answer was covered."
                />
                <MetricCard
                  label="Relevance"
                  value={formatScore(summary.relevance)}
                  suffix="/ 5"
                  status={scoreStatus(summary.relevance)}
                  fill={summary.relevance / 5}
                  hint="Whether the answer stayed on topic."
                />
              </section>

              <section className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                <CategoryBarChart
                  title="Average MRR by category"
                  description="Higher is better. A value of 1.0 means the first retrieved chunk already held the keyword."
                  data={mrrByCategory}
                  max={1}
                  statusOf={ratioStatus}
                  formatValue={formatRatio}
                />
                <CategoryBarChart
                  title="Average accuracy by category"
                  description="Judge score from 1 to 5, compared against the human written reference answers."
                  data={accuracyByCategory}
                  max={5}
                  statusOf={scoreStatus}
                  formatValue={formatScore}
                />
              </section>
            </div>
          )}
        </div>

        <section className="mt-12 border-t border-border pt-8">
          <h2 className="font-heading text-lg font-semibold text-text-primary">
            Recent Activity
          </h2>
          <p className="mt-1.5 text-sm text-text-secondary">
            Questions asked from the chat page, newest first. These are live
            interactions, not graded evaluation runs.
          </p>

          <div className="mt-5">
            {activityState === "loading" && (
              <div className="h-40 animate-pulse rounded-xl border border-border bg-bg-panel" />
            )}

            {activityState === "error" && (
              <EmptyState
                title="Could not load activity"
                description="The chat log could not be read from the backend."
              />
            )}

            {activityState === "ready" && activity.length === 0 && (
              <EmptyState
                title="No chat activity yet"
                description="Ask a question on the chat page and it will show up here."
              />
            )}

            {activityState === "ready" && activity.length > 0 && (
              <ul className="overflow-hidden rounded-xl border border-border bg-bg-panel">
                {activity.map((entry, index) => (
                  <ActivityRow
                    key={`${entry.timestamp}-${index}`}
                    entry={entry}
                  />
                ))}
              </ul>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="flex flex-col gap-6" aria-busy>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-5">
        {Array.from({ length: 5 }, (_, index) => (
          <div
            key={index}
            className="h-32 animate-pulse rounded-xl border border-border bg-bg-panel"
          />
        ))}
      </div>
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {Array.from({ length: 2 }, (_, index) => (
          <div
            key={index}
            className="h-80 animate-pulse rounded-xl border border-border bg-bg-panel"
          />
        ))}
      </div>
    </div>
  );
}
