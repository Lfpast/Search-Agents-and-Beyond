import json
import argparse

def find_improvements(nosearch_file, search_file):
    with open(nosearch_file, 'r') as f:
        nosearch = json.load(f)

    with open(search_file, 'r') as f:
        search = json.load(f)

    nosearch_map = {item['id']: item for item in nosearch['detailed_results']}
    search_map = {item['id']: item for item in search['detailed_results']}

    improved = []
    for id, s_res in search_map.items():
        ns_res = nosearch_map.get(id)
        if ns_res and s_res['correct'] and not ns_res['correct']:
            improved.append({
                'id': id,
                'question': s_res['question'],
                'nosearch_answer': ns_res['student_answer'],
                'search_answer': s_res['student_answer'],
                'ground_truths': s_res['ground_truths']
            })

    print(f"Found {len(improved)} improved cases.")
    for case in improved[:5]:
        print(f"ID: {case['id']}")
        print(f"Question: {case['question']}")
        print(f"Nosearch: {case['nosearch_answer']}")
        print(f"Search: {case['search_answer']}")
        print(f"Ground Truths: {case['ground_truths']}")
        print("-" * 40)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find improvements from nosearch to search results.")
    parser.add_argument('--nosearch', required=True, help='Path to nosearch grading results JSON file')
    parser.add_argument('--search', required=True, help='Path to search grading results JSON file')

    args = parser.parse_args()
    find_improvements(args.nosearch, args.search)
