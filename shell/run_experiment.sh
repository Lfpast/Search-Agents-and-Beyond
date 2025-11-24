#!/bin/bash

# Define paths and settings - modify these as needed
DATA_PATH="../data/nq_test_100.jsonl"
RESULTS_DIR="../results"
MODEL="deepseek-chat"
MAX_WORKERS=8

# Ensure results directory exists
mkdir -p $RESULTS_DIR

# Function to run pipeline for a setting
run_setting() {
    SETTING=$1
    PRED_FILE="$RESULTS_DIR/predictions_${SETTING}.jsonl"
    TRAJ_FILE="$RESULTS_DIR/trajectories_${SETTING}.jsonl"
    SCORE_EM_FILE="$RESULTS_DIR/score_${SETTING}.json"
    SCORE_JUDGE_FILE="$RESULTS_DIR/grading_llm_judge_${SETTING}.json"

    echo "============================================================"
    echo "Running pipeline for setting: $SETTING"
    echo "============================================================"

    # 1. Generate Predictions
    echo "Generating predictions..."
    export PYTHONPATH=.
    python ../scripts/generate_predictions.py \
        --data_path "$DATA_PATH" \
        --output_prediction_path "$PRED_FILE" \
        --output_trajectory_path "$TRAJ_FILE" \
        --setting "$SETTING" \
        --model "$MODEL" \
        --max_workers "$MAX_WORKERS"

    # 2. Evaluate with Exact Match
    echo "Evaluating with Exact Match..."
    python ../scripts/grade_with_em.py \
        --input "$PRED_FILE" \
        --output "$SCORE_EM_FILE"

    # 3. Evaluate with LLM Judge
    # Note: Requires OPENAI_API_KEY or DeepSeek-API in .env
    # We extract the key from .env if not set
    if [ -z "$OPENAI_API_KEY" ]; then
        if [ -f ../.env ]; then
            export OPENAI_API_KEY=$(grep DeepSeek-API ../.env | cut -d '=' -f2 | xargs)
        fi
    fi

    echo "Evaluating with LLM Judge..."
    python ../scripts/grade_with_llm_judge.py \
        --input "$PRED_FILE" \
        --model "$MODEL" \
        --output "$SCORE_JUDGE_FILE"
    
    echo "Completed setting: $SETTING"
    echo ""
}

# Run for both settings
run_setting "nosearch"
run_setting "search"

echo "All experiments completed."
