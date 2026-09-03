import requests
import json
import time
from tabulate import tabulate

# Update this to your live Render endpoint root URL string
BASE_URL = "https://onrender.com"

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
    print("🚀 Initializing Multi-Configuration RAG Evaluation Run...")
    print("=" * 90)
    
    table_rows = []
    
    semantic_retrieval_successes = 0
    pipeline_retrieval_successes = 0
    correct_refusals = 0
    total_unanswerable = 0
    
    for idx, case in enumerate(EVAL_DATASET, 1):
        query = case["q"]
        expected_page = case["exp_page"]
        q_type = case["type"]
        
        print(f"🔄 [{idx}/{len(EVAL_DATASET)}] Evaluating Query: '{query}'")
        
        # 1. Test Configuration A: Raw Semantic Vector Search
        compare_url = f"{BASE_URL}/compare"
        try:
            comp_res = requests.get(compare_url, params={"query": query, "top_k": 3}, timeout=15)
            comp_data = comp_res.json() if comp_res.status_code == 200 else {}
        except Exception:
            comp_data = {}

        # Parse what pages raw vector search found
        semantic_pages = [chunk["metadata"]["page_number"] for chunk in comp_data.get("real_semantic_vector_output", [])]
        semantic_retrieved_correct = expected_page in semantic_pages if expected_page else True
        if q_type != "Unanswerable" and semantic_retrieved_correct:
            semantic_retrieval_successes += 1

        # 2. Test Configuration B: Production Hybrid + Reranking + Ask Answer Pipeline
        ask_url = f"{BASE_URL}/ask"
        try:
            ask_res = requests.get(ask_url, params={"query": query, "top_k": 3}, timeout=15)
            ask_data = ask_res.json() if ask_res.status_code == 200 else {}
        except Exception:
            ask_data = {}
            
        answer_text = ask_data.get("answer", "ERROR")
        pipeline_sources = [src["page_number"] for src in ask_data.get("sources", [])]
        pipeline_retrieved_correct = expected_page in pipeline_sources if expected_page else True
        if q_type != "Unanswerable" and pipeline_retrieved_correct:
            pipeline_retrieval_successes += 1
            
        # 3. Assess Generation Behavior
        generation_verdict = "CORRECT_ANSWER"
        if q_type == "Unanswerable":
            total_unanswerable += 1
            if "cannot find the answer" in answer_text.lower():
                generation_verdict = "CORRECT_REFUSAL ✅"
                correct_refusals += 1
            else:
                generation_verdict = "HALLUCINATION / FAILED REFUSAL ❌"
        else:
            if "cannot find the answer" in answer_text.lower():
                generation_verdict = "FALSE_NEGATIVE_MISS ❌"
            elif expected_page not in pipeline_sources:
                generation_verdict = "UNSUPPORTED_BY_SOURCES ⚠️"

        table_rows.append([
            case["id"],
            q_type,
            "PASS" if semantic_retrieved_correct else "FAIL",
            "PASS" if pipeline_retrieved_correct else "FAIL",
            generation_verdict
        ])
        
        # Throttle pacing interval to remain safely below Gemini free-tier rate limits
        time.sleep(2.0)

    # Output comparative results matrix table
    headers = ["ID", "Query Category", "Semantic Retrieval", "Hybrid+Rerank Retrieval", "Generation Integrity Verdict"]
    print("\n" + "=" * 95)
    print("📋 RAG EVALUATION MATRIX REPORT")
    print("=" * 95)
    print(tabulate(table_rows, headers=headers, tablefmt="grid"))
    
    # Calculate performance metrics summary card
    total_valid = len(EVAL_DATASET) - total_unanswerable
    print("\n📊 CONFIGURATION PERFORMANCE COMPARISON SUMMARY:")
    print("-" * 50)
    print(f"🔹 Raw Semantic Search Retrieval Rate:    {(semantic_retrieval_successes / total_valid) * 100:.1f}% ({semantic_retrieval_successes}/{total_valid})")
    print(f"🔹 Hybrid + Reranked Pipeline Retrieval:  {(pipeline_retrieval_successes / total_valid) * 100:.1f}% ({pipeline_retrieval_successes}/{total_valid})")
    print(f"🔹 Correct Unanswerable Refusal Accuracy:  {(correct_refusals / total_unanswerable) * 100:.1f}% ({correct_refusals}/{total_unanswerable})")
    print("=" * 95)

if __name__ == "__main__":
    run_evaluation_suite()
