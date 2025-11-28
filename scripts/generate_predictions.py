import argparse
import json
import os
import sys
import logging
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Add the parent directory to Python path to import src modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent import SearchAgent

# Thread-safe lock for file writing
write_lock = threading.Lock()

# Disable all logging output from agent during generation
logging.getLogger("src.agent").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("bs4").setLevel(logging.ERROR)

def load_problems(data_path: str) -> list:
    """Load problems from JSONL file."""
    problems = []
    with open(data_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                problems.append(json.loads(line))
    return problems

def generate_predictions(agent, problems: list, output_path: str, trajectory_path: str, max_workers: int):
    """Generate predictions using the agent and save to JSONL with parallel requests."""
    
    # Pre-open files for writing
    pred_file = open(output_path, 'w', encoding='utf-8')
    traj_file = open(trajectory_path, 'w', encoding='utf-8')
    
    def solve_problem(problem):
        """Solve a single problem and return the prediction and trajectory."""
        try:
            result = agent.solve(problem['question'])
            
            # Construct prediction object
            prediction = {
                "id": problem["id"],
                "question": problem["question"],
                "answers": problem["answers"],
                "llm_response": result["final_answer"]
            }
            
            # Construct trajectory object
            steps = []
            for call in result["tool_calls"]:
                action_type = call.get("tool", "search")
                
                step_info = {
                    "step_number": call["step"],
                    "action": action_type,
                }
                
                if action_type == "google_search":
                    step_info["query"] = call.get("query")
                    step_info["retrieved_documents"] = call.get("retrieved_documents", [])
                elif action_type == "browse_website":
                    step_info["url"] = call.get("url")
                    step_info["content_snippet"] = call.get("result", "")[:200]
                
                steps.append(step_info)
            
            trajectory = {
                "id": problem["id"],
                "question": problem["question"],
                "ground_truths": problem["answers"],
                "trajectory": {
                    "question": problem["question"],
                    "steps": steps,
                    "final_answer": result["final_answer"],
                    "total_search_steps": len(steps)
                }
            }
            
            return prediction, trajectory
            
        except Exception as e:
            print(f"Error solving problem {problem['id']}: {e}")
            return None, None
    
    # Execute tasks in parallel with progress bar
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(solve_problem, problem): problem for problem in problems}
        
        with tqdm(total=len(problems), desc="Generating predictions") as pbar:
            for future in as_completed(futures):
                prediction, trajectory = future.result()
                
                if prediction and trajectory:
                    # Thread-safe file writing
                    with write_lock:
                        pred_file.write(json.dumps(prediction, ensure_ascii=False) + "\n")
                        traj_file.write(json.dumps(trajectory, ensure_ascii=False) + "\n")
                        # Flush to ensure data is written immediately (optional but good for debugging)
                        pred_file.flush()
                        traj_file.flush()
                
                pbar.update(1)
    
    pred_file.close()
    traj_file.close()

def main():
    parser = argparse.ArgumentParser(description="Generate NQ predictions")
    parser.add_argument("--data_path", type=str, required=True, help="Path to input JSONL data file")
    parser.add_argument("--output_prediction_path", type=str, required=True, help="Path to save predictions JSONL file")
    parser.add_argument("--output_trajectory_path", type=str, required=True, help="Path to save trajectories JSONL file")
    parser.add_argument("--setting", type=str, choices=["nosearch", "search", "browsing"], required=True,
                       help="Setting: 'nosearch' (baseline), 'search' (with search tool), or 'browsing' (with search and browsing tools)")
    parser.add_argument("--model", type=str, default="deepseek-chat", help="Model name")
    parser.add_argument("--max_workers", type=int, default=4, help="Number of parallel workers")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of problems for testing")

    args = parser.parse_args()

    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output_prediction_path), exist_ok=True)
    os.makedirs(os.path.dirname(args.output_trajectory_path), exist_ok=True)

    # Load problems
    problems = load_problems(args.data_path)
    if args.limit:
        problems = problems[:args.limit]
    print(f"Loaded {len(problems)} problems")

    # Configure agent based on setting
    if args.setting == "nosearch":
        agent = SearchAgent(use_tools=False, max_steps=1, temperature=0.0, model=args.model)
    elif args.setting == "search":
        agent = SearchAgent(use_tools=True, use_browsing=False, max_steps=10, temperature=0.0, model=args.model)
    elif args.setting == "browsing":
        agent = SearchAgent(use_tools=True, use_browsing=True, max_steps=10, temperature=0.0, model=args.model)

    # Generate predictions
    print(f"Generating {args.setting} predictions...")
    generate_predictions(agent, problems, args.output_prediction_path, args.output_trajectory_path, args.max_workers)
    print(f"Predictions saved to {args.output_prediction_path}")
    print(f"Trajectories saved to {args.output_trajectory_path}")

if __name__ == "__main__":
    main()
