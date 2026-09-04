# Nexara RAG

A retrieval augmented generation system that runs entirely on the local
machine, with a real evaluation harness attached to it. Documents are
embedded and stored locally with ChromaDB, inference runs through Ollama,
and no request leaves the machine. The corpus is a set of invented
documents for a fictional logistics company called Nexara, which exists so
that retrieval can be tested against facts that are specific, checkable,
and guaranteed to be absent from any model's training data. The system is
written without LangChain or any comparable framework: retrieval, chunking,
prompt construction, re-ranking, and scoring are all implemented directly.

## Architecture

### Ingestion

`backend/ingest.py` walks `nexara-docs/`, treating each subdirectory name
(`company`, `products`, `employees`, `contracts`) as a document type tag
carried through as metadata. Files are split on paragraph boundaries into
chunks of up to 500 characters, with the trailing 100 characters of the
previous chunk prepended to each one so a fact split across a boundary is
still reachable from both sides. Every chunk is embedded with
`nomic-embed-text` and written to a persistent ChromaDB collection named
`docs` in `backend/vector_db/`, alongside its source path and doc type.

### Basic pipeline

`backend/answer_basic.py` is the straightforward implementation: embed the
question with the same model used at ingestion, ask Chroma for the 5
nearest chunks, concatenate them into a system prompt, and generate. One
embedding call and one chat call per question. This is what the live chat
endpoint serves, because it answers in a few seconds.

### Pro pipeline

`backend/answer.py` adds three techniques on top of the same vector store.

1. **Query rewriting.** The raw question is passed to the model first and
   rewritten into a standalone search query. This matters for follow-ups
   such as "what about their pricing" that are not searchable on their own.
2. **Dual search.** Both the original question and the rewritten query are
   embedded and searched separately, at a wider `RETRIEVAL_K` of 15. The
   two result sets are merged and deduplicated by chunk text, so a chunk
   that only one phrasing surfaces still makes it through.
3. **Re-ranking.** The merged set is handed back to the model, which
   re-orders the chunks by relevance to the original question, not the
   rewrite. The response is constrained to a Pydantic schema holding a list
   of chunk ids, so the output cannot drift into prose. The top
   `FINAL_K` of 5 are kept and used as context.

The cost is four or more model calls per question instead of two, which is
why the two pipelines coexist rather than one replacing the other.

### Evaluation

`backend/tests.jsonl` holds 15 questions, each with a list of keywords that
must appear in the retrieved chunks, a human written reference answer, and
a category: `direct_fact`, `spanning`, `relationship`, `numerical`, or
`temporal`. The categories exist so that failures can be attributed. A
question that needs facts from two documents is a different retrieval
problem from one that needs a single sentence, and averaging them together
hides that.

`backend/run_eval.py` scores two things independently.

**Retrieval, arithmetic only, no model involved.** Mean reciprocal rank is
computed per keyword: 1.0 if the keyword appears in the first retrieved
chunk, 0.5 in the second, 0.33 in the third, 0 if it never appears, then
averaged across the keywords for that question. Keyword coverage is the
share of expected keywords found anywhere in the retrieved set. MRR asks
whether ranking is correct, coverage asks whether the information arrived
at all. A high coverage with a low MRR means the retriever is finding the
right documents and ordering them badly.

**Answer quality, model as judge.** The generated answer and the reference
answer are given to the model, which returns accuracy, completeness, and
relevance on a 1 to 5 scale. The response is pinned to a Pydantic schema,
so the judge returns integers rather than an essay. Results are written to
`backend/eval_results.json` as per question rows plus a summary.

Separating the two matters. When an answer is wrong, the retrieval scores
say whether the context was missing or whether the generator had the facts
and failed anyway.

### Backend

`backend/app.py` is a FastAPI application with two endpoints. `POST /ask`
takes `{question}` and returns the answer with the list of sources it was
built from. `GET /eval-results` serves the stored evaluation run. CORS is
open to `http://localhost:3000` only, since the frontend is served from a
different port and would otherwise be blocked by the browser.

### Frontend

`frontend/` is a Next.js App Router application with two pages. The chat
page posts questions and renders answers with source chips showing which
files backed each response. The dashboard reads `/eval-results` and shows
five summary metric cards plus bar charts of average MRR and average
accuracy broken down by question category, which is where the category
tags earn their place.

## Tech stack

- Python 3.12, managed with uv
- Ollama for all inference, running `llama3.1:8b` for chat, re-ranking,
  query rewriting, and judging, and `nomic-embed-text` for embeddings
- ChromaDB as the persistent vector store
- Pydantic for structured model output and request validation
- FastAPI and uvicorn for the API
- Next.js 15, React 19, TypeScript
- Tailwind CSS v4
- recharts for the dashboard charts

## Why no LangChain

LangChain would have collapsed most of this into a handful of calls. It was
left out on purpose.

The interesting parts of a RAG system are the parts a framework hides.
Chunk boundaries decide what can be retrieved at all. Whether re-ranking
runs against the original question or the rewritten one changes the
results. Whether a judge returns a number or a paragraph decides whether
the evaluation can be aggregated. Writing these directly means each choice
is visible in the code and can be changed and measured, instead of being a
default inside a dependency.

The practical benefit showed up during evaluation. When the pro pipeline
scored worse than the basic one, the cause was findable, because every step
between question and answer is a function in this repository. Debugging the
same regression through a framework's abstractions would have been
considerably slower.

## Setup

### 1. Install Ollama

Download from [ollama.com](https://ollama.com), then confirm the service is
running. It listens on port 11434.

### 2. Pull the models

```
ollama pull llama3.1:8b
ollama pull nomic-embed-text
```

### 3. Install Python dependencies

From the repository root:

```
uv sync
```

### 4. Build the vector store

`ingest.py` resolves `nexara-docs/` and `vector_db/` relative to the working
directory, so run it from `backend/`:

```
cd backend
uv run python ingest.py
```

Re-run this after editing anything in `nexara-docs/`. Chunks are written
with positional ids, so if a re-run produces fewer chunks than the previous
one, delete `vector_db/` first rather than writing over the old collection.

### 5. Start the backend

```
cd backend
uv run uvicorn app:app --reload --port 8000
```

`app.py` reads `eval_results.json` by relative path, so it also needs to be
started from `backend/`.

### 6. Start the frontend

```
cd frontend
npm install
npm run dev
```

The chat page is at `http://localhost:3000` and the dashboard at
`http://localhost:3000/dashboard`. Port 3000 is not optional unless the
`allow_origins` list in `app.py` is changed to match, since the backend
rejects other origins.

### Running an evaluation

```
cd backend
uv run python run_eval.py
```

This runs all 15 questions through the pro pipeline twice, once to score
retrieval and once to generate and judge an answer, so it takes a while. It
writes `eval_results.json`, which the dashboard then picks up.

## Findings

**The pro techniques are not free, and they are not always an
improvement.** Query rewriting, dual search, and re-ranking made results
worse on `llama3.2:3b` and better on `llama3.1:8b`. The reason is that all
three steps are themselves reasoning tasks delegated to the model. A
rewritten query is only useful if the rewrite preserves the intent of the
original. A re-ranking is only useful if the model can actually judge
relevance. On the 3B model these steps introduced errors: rewrites drifted
away from what was asked, and re-ranking moved correct chunks down. The
techniques amplify model capability rather than substituting for it, and
below some capability threshold they amplify the wrong thing.

This is also why `app.py` serves the basic pipeline rather than the pro one.
The pro pipeline makes at least four sequential model calls per question,
which is acceptable in a batch evaluation and slow in an interactive chat.

**Separating retrieval scores from answer scores was worth the effort.**
The two failure modes look identical from the outside. Cases where keyword
coverage was 1.0 and the judged accuracy was still 1 out of 5 are the
useful ones: the retriever did its job and the generator did not. Without
the split, those would have been indistinguishable from retrieval misses,
and the obvious next move would have been to tune chunking, which would
have fixed nothing.

**Keyword based retrieval scoring is cheap and blunt.** MRR here is measured
by substring presence, which says a keyword was in the chunk, not that the
chunk answered the question. It is fast, deterministic, and needs no model,
which makes it useful as a regression check across pipeline changes. It is
not a measure of retrieval quality in any deeper sense.

### Current state of the stored run

`eval_results.json` currently holds a partial run: 4 of the 15 questions,
all of them `direct_fact`. The dashboard renders it correctly but both
charts show a single category. A full run is needed before the per category
comparison means anything.

## Repository layout

```
rag-lab/
  backend/
    nexara-docs/        source documents, one folder per doc type
    vector_db/          persistent ChromaDB store, created by ingest.py
    ingest.py           chunking and embedding
    answer_basic.py     single search pipeline, used by the API
    answer.py           rewriting, dual search, re-ranking
    app.py              FastAPI endpoints
    run_eval.py         evaluation harness
    tests.jsonl         15 test questions with keywords and references
    eval_results.json   output of the last evaluation run
    visualize.py        t-SNE plot of the embedding space
  frontend/
    src/app/            chat page and dashboard page
    src/components/     MetricCard, ChatMessage, SourceChip, charts
    src/lib/            typed API client and metric helpers
```
