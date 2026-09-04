import requests
import json
import time
from tabulate import tabulate

BASE_URL = "https://multi-user-expense-tracker-api.onrender.com/search"

EVAL_DATASET = [
    {"id": "Q1", "type": "Easy", "q": "Who issued this manual framework?", "exp_page": 1},
    {"id": "Q2", "type": "Easy", "q": "When does this startup policy become effective?", "exp_page": 1},
    {"id": "Q3", "type": "Easy", "q": "What is the classification level of this file?", "exp_page": 1},
    {"id": "Q4", "type": "Exact", "q": "What is the specific registry identifier key for engineering?", "exp_page": 2},
    {"id": "Q5", "type": "Exact", "q": "Which section covers IT Asset Configurations?", "exp_page": 2},
    {"id": "Q6", "type": "Exact", "q": "Under what specific clause is the system registration token written?", "exp_page": 2},
    {"id": "Q7", "type": "Semantic", "q": "Where can I find info regarding overnight sleep caps?", "exp_page": 3},
    {"id": "Q8", "type": "Semantic", "q": "How many days do I have to submit food bills from a diner?", "exp_page": 3},
    {"id": "Q9", "type": "Semantic", "q": "Is there a stipend for setting up a home workspace?", "exp_page": 3},
    {"id": "Q10", "type": "Semantic", "q": "Do remote equipment allocations require manager sign-offs?", "exp_page": 3},
    {"id": "Q11", "type": "Unanswerable", "q": "What is the policy limit for international business class flights?", "exp_page": None},
    {"id": "Q12", "type": "Unanswerable", "q": "How much equity do software engineer interns receive?", "exp_page": None},
    {"id": "Q13", "type": "Unanswerable", "q": "What is the company maternity leave timeline restriction?", "exp_page": None},
    {"id": "Q14", "type": "Exact", "q": "To which specific app should restaurant bills be pushed?", "exp_page": 3},
    {"id": "Q15", "type": "Semantic", "q": "What items are considered valid assets under Clause 2.B?", "exp_page": 3}
]

def run_evaluation_suite():
    print("🚀 Initializing LangChain Production RAG Evaluation Suite...")
    print("=" * 95)
    
    table_rows = []
    pipeline_retrieval_successes = 0
    correct_refusals = 0
    total_unanswerable = 0
    
    for idx, case in enumerate(EVAL_DATASET, 1):
        query = case["q"]
        expected_page = case["exp_page"]
        q_type = case["type"]
        
        print(f"🔄 [{idx}/{len(EVAL_DATASET)}] Evaluating Query: '{query}'")
        
        # Query your updated live conversational LangChain endpoint
        ask_url = f"{BASE_URL}/ask"
        try:
            # We pass top_k=3 to retrieve background items fairly
            ask_res = requests.get(ask_url, params={"query": query, "top_k": 3}, timeout=15)
            ask_data = ask_res.json() if ask_res.status_code == 200 else {}
        except Exception:
            ask_data = {}
            
        answer_text = ask_data.get("answer", "ERROR")
        
        # Extract precise page number integers directly from the active sources dictionary
        pipeline_sources = []
        for src in ask_data.get("sources", []):
            try:
                pipeline_sources.append(int(src["page_number"]))
            except (KeyError, ValueError, TypeError):
                continue

        # For unanswerable queries, retrieval passes if it successfully locks out non-existent pages
        if q_type == "Unanswerable":
            pipeline_retrieved_correct = True
        else:
            pipeline_retrieved_correct = expected_page in pipeline_sources
            
        if q_type != "Unanswerable" and pipeline_retrieved_correct:
            pipeline_retrieval_successes += 1
            
        # Classify Text Generation Integrity Verdicts
        generation_verdict = "CORRECT_ANSWER"
        is_refusal = any(term in answer_text.lower() for term in ["cannot find", "not find", "not provided", "not mention", "don't have info", "no information", "not trace", "sorry"])
        
        if q_type == "Unanswerable":
            total_unanswerable += 1
            if is_refusal:
                generation_verdict = "CORRECT_REFUSAL ✅"
                correct_refusals += 1
            else:
                generation_verdict = "HALLUCINATION / FAILED REFUSAL ❌"
        else:
            if is_refusal:
                generation_verdict = "FALSE_NEGATIVE_MISS ❌"
            elif expected_page not in pipeline_sources:
                generation_verdict = "UNSUPPORTED_BY_SOURCES ⚠️"

        table_rows.append([
            case["id"],
            q_type,
            "PASS" if pipeline_retrieved_correct else "FAIL",
            generation_verdict
        ])
        
        # Small delay to keep free tier quotas refreshed and healthy
        time.sleep(1.0)

    headers = ["ID", "Query Category", "LangChain Pipeline Retrieval", "Generation Integrity Verdict"]
    print("\n" + "=" * 95)
    print("📋 LANGCHAIN RAG EVALUATION MATRIX REPORT")
    print("=" * 95)
    print(tabulate(table_rows, headers=headers, tablefmt="grid"))
    
    total_valid = len(EVAL_DATASET) - total_unanswerable
    print("\n📊 CONFIGURATION PERFORMANCE COMPARISON SUMMARY:")
    print("-" * 50)
    print(f"🔹 LangChain Hybrid FAISS Retrieval Rate:  {(pipeline_retrieval_successes / total_valid) * 100:.1f}% ({pipeline_retrieval_successes}/{total_valid})")
    print(f"🔹 Correct Unanswerable Refusal Accuracy:  {(correct_refusals / total_unanswerable) * 100:.1f}% ({correct_refusals}/{total_unanswerable})")
    print("=" * 95)

if __name__ == "__main__":
    run_evaluation_suite()
