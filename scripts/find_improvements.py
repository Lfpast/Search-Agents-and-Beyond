import json

with open('results/grading_llm_judge_nosearch.json', 'r') as f:
    nosearch = json.load(f)

with open('results/grading_llm_judge_search.json', 'r') as f:
    search = json.load(f)

nosearch_map = {item['id']: item for item in nosearch['detailed_results']}
search_map = {item['id']: item for item in search['detailed_results']}

improved = []
for id, s_res in search_map.items():
    ns_res = nosearch_map.get(id)
    if s_res['correct'] and not ns_res['correct']:
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
