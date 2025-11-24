#!/bin/bash
echo ""
echo "============================================================"
echo "Running Improvement Analysis"
echo "============================================================"

# Define the file paths here - modify these as needed
NOSearch_FILE="../results/v1/grading_llm_judge_nosearch.json"
SEARCH_FILE="../results/v1/grading_llm_judge_search.json"

# Run the Python script with the defined paths
python ../scripts/find_improvements.py --nosearch "$NOSearch_FILE" --search "$SEARCH_FILE"