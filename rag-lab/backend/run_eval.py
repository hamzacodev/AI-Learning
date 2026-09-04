import json
import ollama
from pydantic import BaseModel

# Import from your BASIC RAG (fast). Later we'll switch to answer.py (pro).
from answer import fetch_context, answer_question

JUDGE_MODEL = "llama3.1:8b"     # our LLM-as-a-judge
TEST_FILE = "tests.jsonl"


# --- DATA SHAPES ---
class TestQuestion(BaseModel):
    """One row from tests.jsonl"""
    question: str
    keywords: list[str]
    reference_answer: str
    category: str


class AnswerJudgment(BaseModel):
    """Locks the judge LLM's response into strict scores."""
    accuracy: int         # 1-5, is it factually correct?
    completeness: int      # 1-5, did it cover everything the reference did?
    relevance: int         # 1-5, did it stay on topic?
    feedback: str          # short written comment


# --- LOAD TESTS ---
def load_tests() -> list[TestQuestion]:
    tests = []
    with open(TEST_FILE, "r") as f:
        for line in f:
            data = json.loads(line)
            tests.append(TestQuestion(**data))
    return tests


# --- RETRIEVAL SCORING (pure math, no LLM) ---
def calculate_mrr(keyword: str, retrieved_chunks) -> float:
    """
    Mean Reciprocal Rank for ONE keyword.
    If it's found in the 1st chunk: 1.0
    2nd chunk: 0.5
    3rd chunk: 0.33
    Not found: 0.0
    """
    keyword_lower = keyword.lower()
    for rank, chunk in enumerate(retrieved_chunks, start=1):
        if keyword_lower in chunk.text.lower():
            return 1.0 / rank
    return 0.0


def calculate_keyword_coverage(keywords: list[str], retrieved_chunks) -> float:
    """% of keywords that appear ANYWHERE in the retrieved chunks."""
    all_text = " ".join(c.text for c in retrieved_chunks).lower()
    found = sum(1 for kw in keywords if kw.lower() in all_text)
    return found / len(keywords) if keywords else 0.0


def evaluate_retrieval(test: TestQuestion) -> dict:
    """Run retrieval on one test question, score it."""
    chunks = fetch_context(test.question)
    mrr_scores = [calculate_mrr(kw, chunks) for kw in test.keywords]
    return {
        "mrr": sum(mrr_scores) / len(mrr_scores) if mrr_scores else 0.0,
        "keyword_coverage": calculate_keyword_coverage(test.keywords, chunks),
        "category": test.category,
    }


# --- ANSWER SCORING (LLM-as-a-judge) ---
def evaluate_answer(test: TestQuestion) -> dict:
    """Run the full RAG pipeline, then have an LLM grade the answer."""
    generated, _ = answer_question(test.question)

    judge_prompt = f"""You are grading a RAG system's answer.

QUESTION: {test.question}

REFERENCE ANSWER (the correct answer, written by a human):
{test.reference_answer}

GENERATED ANSWER (what the RAG system produced):
{generated}

Score the generated answer on three dimensions, each 1-5:
- accuracy: how factually correct compared to the reference (any wrong fact = 1)
- completeness: did it cover everything the reference covers
- relevance: did it stay on-topic vs. going off on tangents

Also provide short feedback (one sentence)."""

    response = ollama.chat(
        model=JUDGE_MODEL,
        messages=[{"role": "user", "content": judge_prompt}],
        format=AnswerJudgment.model_json_schema(),
    )
    scores = AnswerJudgment.model_validate_json(response["message"]["content"])
    return {
        "accuracy": scores.accuracy,
        "completeness": scores.completeness,
        "relevance": scores.relevance,
        "category": test.category,
    }


# --- MAIN RUNNER ---
def run_full_evaluation(): 
    tests = load_tests()[:4]
    print(f"Loaded {len(tests)} test questions\n")

    retrieval_results = []
    answer_results = []

    for i, test in enumerate(tests, start=1):
        print(f"[{i}/{len(tests)}] {test.question[:60]}...")

        r_score = evaluate_retrieval(test)
        retrieval_results.append(r_score)
        print(f"  Retrieval → MRR: {r_score['mrr']:.2f}, coverage: {r_score['keyword_coverage']:.0%}")

        a_score = evaluate_answer(test)
        answer_results.append(a_score)
        print(f"  Answer → acc: {a_score['accuracy']}, comp: {a_score['completeness']}, rel: {a_score['relevance']}\n")

    # OVERALL SCORES
    avg_mrr = sum(r["mrr"] for r in retrieval_results) / len(retrieval_results)
    avg_coverage = sum(r["keyword_coverage"] for r in retrieval_results) / len(retrieval_results)
    avg_acc = sum(a["accuracy"] for a in answer_results) / len(answer_results)
    avg_comp = sum(a["completeness"] for a in answer_results) / len(answer_results)
    avg_rel = sum(a["relevance"] for a in answer_results) / len(answer_results)

    print("=" * 50)
    print("OVERALL SCORES")
    print("=" * 50)
    print(f"Retrieval MRR:       {avg_mrr:.4f}")
    print(f"Keyword Coverage:    {avg_coverage:.1%}")
    print(f"Answer Accuracy:     {avg_acc:.2f}/5")
    print(f"Answer Completeness: {avg_comp:.2f}/5")
    print(f"Answer Relevance:    {avg_rel:.2f}/5")
    # Save results to disk so we can compare runs and feed a dashboard later
    with open("eval_results.json", "w") as f:
        json.dump({
            "retrieval": retrieval_results,
            "answers": answer_results,
            "summary": {
                "mrr": avg_mrr,
                "keyword_coverage": avg_coverage,
                "accuracy": avg_acc,
                "completeness": avg_comp,
                "relevance": avg_rel,
            }
        }, f, indent=2)
    print("\nSaved eval_results.json")

if __name__ == "__main__":
    run_full_evaluation()
