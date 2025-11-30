import sys
import os
import json
import logging

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent import SearchAgent

# Configure logging to see tool execution details
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_shopping():
    print(">>> Initializing SearchAgent with Shopping tool enabled...")
    
    try:
        agent = SearchAgent(
            model="deepseek-chat",
            temperature=0.0,
            max_steps=5,
            use_tools=True,
            use_browsing=False, # Focus on shopping for this test
            use_shopping=True
        )
    except ValueError as e:
        print(f"Error initializing agent: {e}")
        return

    # A question likely to trigger the shopping tool
    question = "Can you recommend some Nike Air Max 97 shoes available in Hong Kong and tell me their prices?"
    
    print(f"\n>>> Test Question: {question}")
    print("-" * 60)
    
    # Run the agent
    result = agent.solve(question)
    
    print("-" * 60)
    print("\n>>> Final Answer:")
    print(result["final_answer"])
    
    print("\n>>> Tool Call Trajectory:")
    shopping_called = False
    for step in result["tool_calls"]:
        tool_name = step['tool']
        print(f"\n[Step {step['step']}] Tool Used: {tool_name}")
        
        if tool_name == 'google_shopping':
            shopping_called = True
            print(f"  Query: {step.get('query')}")
            print(f"  Params: num={step.get('num')}, page={step.get('page')}")
            
            items = step.get('shopping_items', [])
            print(f"  Items Found: {len(items)}")
            
            if items:
                print("  Top 3 Items:")
                for i, item in enumerate(items[:3]):
                    print(f"    {i+1}. {item.get('title')} | Price: {item.get('price')} | Source: {item.get('source')}")
        elif tool_name == 'google_search':
             print(f"  Query: {step.get('query')}")

    if shopping_called:
        print("\n✅ SUCCESS: Google Shopping tool was successfully called.")
    else:
        print("\n❌ FAILURE: Google Shopping tool was NOT called.")

if __name__ == "__main__":
    test_shopping()
