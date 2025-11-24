import sys
import os

# Add Project root to path
sys.path.append(os.getcwd())

from src.agent import SearchAgent
from src.tools import google_search

def test_tool_direct():
    print("=== Testing google_search tool directly ===")
    
    # Test 1: Batch Search
    print("\n1. Testing Batch Search (Apple and Tesla)...")
    results = google_search(["Apple Inc", "Tesla Inc"])
    if isinstance(results, list) and len(results) == 2:
        print("✅ Batch search returned 2 results")
    else:
        print(f"❌ Batch search failed: {type(results)}")

    # Test 2: Pagination
    print("\n2. Testing Pagination (Page 2)...")
    results_p1 = google_search("Apple Inc", page=1)
    results_p2 = google_search("Apple Inc", page=2)
    
    # Simple check if results are different (naive check)
    try:
        top_p1 = results_p1.get('organic', [])[0].get('title')
        top_p2 = results_p2.get('organic', [])[0].get('title')
        print(f"Page 1 Top Result: {top_p1}")
        print(f"Page 2 Top Result: {top_p2}")
        if top_p1 != top_p2:
            print("✅ Pagination returned different results")
        else:
            print("⚠️ Pagination returned same top result (might be expected depending on SERP stability)")
    except Exception as e:
        print(f"❌ Pagination test error: {e}")

    # Test 3: Date Range (TBS)
    print("\n3. Testing Date Range (past_24h)...")
    results_tbs = google_search("Apple Inc stock news", tbs="past_24h")
    # Check if we got results (hard to verify date programmatically without parsing, but we check for no error)
    if "organic" in results_tbs:
        print("✅ Date range search returned results")
    else:
        print(f"❌ Date range search failed: {results_tbs}")

def test_agent():
    print("\n=== Testing SearchAgent ===")
    try:
        agent = SearchAgent()
    except Exception as e:
        print(f"Failed to initialize agent: {e}")
        return

    # Question designed to trigger tbs and potentially batch search
    question = "What are the latest (past 24 hours) major headlines for Apple and Tesla?"
    print(f"\nQuestion: {question}")
    
    print("Solving...")
    result = agent.solve(question)
    
    print("\nFinal Answer:")
    print(result["final_answer"])
    
    print("\nReasoning Steps:")
    for step in result["reasoning_steps"]:
        print(f"Step {step['step']}: {step['content'][:100]}...")
        
    print("\nTool Calls:")
    for call in result["tool_calls"]:
        print(f"Tool: {call['tool']}")
        print(f"  Query: {call['query']}")
        print(f"  Page: {call.get('page')}")
        print(f"  TBS: {call.get('tbs')}")

if __name__ == "__main__":
    test_tool_direct()
    test_agent()
