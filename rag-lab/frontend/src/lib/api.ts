/**
 * Typed fetch helpers for the local Python backend.
 *
 * The backend is expected on http://localhost:8000. Override with
 * NEXT_PUBLIC_API_BASE if it is bound somewhere else.
 */

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

/** Answers can take 30 to 60 seconds, so the ceiling is deliberately high. */
const ASK_TIMEOUT_MS = 1000_000; // 10 minutes
const EVAL_TIMEOUT_MS = 20_000;

/* --- Response shapes --- */

export interface Source {
  source: string;
  doc_type: string;
}

/** One earlier turn, in the shape the chat model expects. */
export interface ChatTurn {
  role: "user" | "assistant";
  content: string;
}

export interface AskResponse {
  answer: string;
  sources: Source[];
}

export interface EvalSummary {
  mrr: number;
  keyword_coverage: number;
  accuracy: number;
  completeness: number;
  relevance: number;
}

export interface RetrievalResult {
  mrr: number;
  keyword_coverage: number;
  category: string;
}

export interface AnswerResult {
  accuracy: number;
  completeness: number;
  relevance: number;
  category: string;
}

export interface ChatLogEntry {
  timestamp: string;
  question: string;
  answer: string;
  sources: Source[];
}

export interface EvalResults {
  summary: EvalSummary;
  retrieval: RetrievalResult[];
  answers: AnswerResult[];
}

/* --- Errors --- */

export class ApiError extends Error {
  readonly status?: number;

  constructor(message: string, status?: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

/**
 * Wraps an external signal together with a timeout, so a caller can still
 * cancel early while the request also gives up on its own eventually.
 */
function withTimeout(ms: number, external?: AbortSignal) {
  const controller = new AbortController();
  const timer = setTimeout(
    () => controller.abort(new DOMException("Timeout", "TimeoutError")),
    ms,
  );

  if (external) {
    if (external.aborted) {
      controller.abort(external.reason);
    } else {
      external.addEventListener(
        "abort",
        () => controller.abort(external.reason),
        {
          once: true,
        },
      );
    }
  }

  return { signal: controller.signal, done: () => clearTimeout(timer) };
}

function isAbort(error: unknown): boolean {
  return error instanceof DOMException && error.name === "AbortError";
}

function describeNetworkFailure(): ApiError {
  return new ApiError(
    `Could not reach the backend at ${API_BASE}. Check that it is running.`,
  );
}

/* --- Endpoints --- */

/**
 * POST /ask, returns the generated answer plus the chunks it was built from.
 * `history` carries the earlier turns of the conversation, excluding the
 * question being asked, which travels in its own field.
 */
export async function askQuestion(
  question: string,
  history: ChatTurn[] = [],
  signal?: AbortSignal,
): Promise<AskResponse> {
  const { signal: combined, done } = withTimeout(ASK_TIMEOUT_MS, signal);

  let response: Response;
  try {
    response = await fetch(`${API_BASE}/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, history }),
      signal: combined,
    });
  } catch (error) {
    if (isAbort(error)) throw error;
    throw describeNetworkFailure();
  } finally {
    done();
  }

  if (!response.ok) {
    throw new ApiError(
      `The backend returned ${response.status} ${response.statusText}.`,
      response.status,
    );
  }

  const data: unknown = await response.json();
  return normalizeAskResponse(data);
}

/**
 * GET /eval-results. Resolves to null when the backend has no run stored yet,
 * which the dashboard renders as an empty state rather than an error.
 */
export async function fetchEvalResults(
  signal?: AbortSignal,
): Promise<EvalResults | null> {
  const { signal: combined, done } = withTimeout(EVAL_TIMEOUT_MS, signal);

  let response: Response;
  try {
    response = await fetch(`${API_BASE}/eval-results`, {
      signal: combined,
      cache: "no-store",
    });
  } catch (error) {
    if (isAbort(error)) throw error;
    throw describeNetworkFailure();
  } finally {
    done();
  }

  if (response.status === 404 || response.status === 204) return null;

  if (!response.ok) {
    throw new ApiError(
      `The backend returned ${response.status} ${response.statusText}.`,
      response.status,
    );
  }

  const data: unknown = await response.json();
  return normalizeEvalResults(data);
}

/**
 * GET /chat-log. The backend already returns newest first, and an empty
 * array before any question has been asked, so there is no null case here.
 */
export async function fetchChatLog(
  signal?: AbortSignal,
): Promise<ChatLogEntry[]> {
  const { signal: combined, done } = withTimeout(EVAL_TIMEOUT_MS, signal);

  let response: Response;
  try {
    response = await fetch(`${API_BASE}/chat-log`, {
      signal: combined,
      cache: "no-store",
    });
  } catch (error) {
    if (isAbort(error)) throw error;
    throw describeNetworkFailure();
  } finally {
    done();
  }

  if (response.status === 404 || response.status === 204) return [];

  if (!response.ok) {
    throw new ApiError(
      `The backend returned ${response.status} ${response.statusText}.`,
      response.status,
    );
  }

  const data: unknown = await response.json();
  return normalizeChatLog(data);
}

/* --- Normalizers, so a partial payload cannot crash the render --- */

function num(value: unknown): number {
  return typeof value === "number" && Number.isFinite(value) ? value : 0;
}

function str(value: unknown, fallback = ""): string {
  return typeof value === "string" ? value : fallback;
}

function normalizeAskResponse(data: unknown): AskResponse {
  const raw = (data ?? {}) as Record<string, unknown>;
  const sources = Array.isArray(raw.sources) ? raw.sources : [];

  return {
    answer: str(raw.answer),
    sources: sources.map((entry) => {
      const item = (entry ?? {}) as Record<string, unknown>;
      return {
        source: str(item.source, "unknown"),
        doc_type: str(item.doc_type, "unknown"),
      };
    }),
  };
}

function normalizeEvalResults(data: unknown): EvalResults | null {
  const raw = (data ?? {}) as Record<string, unknown>;
  if (!raw.summary || typeof raw.summary !== "object") return null;

  const summary = raw.summary as Record<string, unknown>;
  const retrieval = Array.isArray(raw.retrieval) ? raw.retrieval : [];
  const answers = Array.isArray(raw.answers) ? raw.answers : [];

  return {
    summary: {
      mrr: num(summary.mrr),
      keyword_coverage: num(summary.keyword_coverage),
      accuracy: num(summary.accuracy),
      completeness: num(summary.completeness),
      relevance: num(summary.relevance),
    },
    retrieval: retrieval.map((entry) => {
      const item = (entry ?? {}) as Record<string, unknown>;
      return {
        mrr: num(item.mrr),
        keyword_coverage: num(item.keyword_coverage),
        category: str(item.category, "uncategorized"),
      };
    }),
    answers: answers.map((entry) => {
      const item = (entry ?? {}) as Record<string, unknown>;
      return {
        accuracy: num(item.accuracy),
        completeness: num(item.completeness),
        relevance: num(item.relevance),
        category: str(item.category, "uncategorized"),
      };
    }),
  };
}

function normalizeChatLog(data: unknown): ChatLogEntry[] {
  if (!Array.isArray(data)) return [];

  return data.map((entry) => {
    const item = (entry ?? {}) as Record<string, unknown>;
    const sources = Array.isArray(item.sources) ? item.sources : [];

    return {
      timestamp: str(item.timestamp),
      question: str(item.question),
      answer: str(item.answer),
      sources: sources.map((raw) => {
        const source = (raw ?? {}) as Record<string, unknown>;
        return {
          source: str(source.source, "unknown"),
          doc_type: str(source.doc_type, "unknown"),
        };
      }),
    };
  });
}
