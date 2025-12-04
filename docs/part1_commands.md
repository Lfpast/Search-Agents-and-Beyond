## Part I Command Cheatsheet: Search-Augmented QA

This file collects commonly used commands for **Part I** of the project (QA system with and without search), so they can be copy–pasted and run directly.  
All commands assume the working directory is the project root:  
`/Users/liuzihe/Desktop/comp4901b/COMP4901B_Project`.

---

## 0. Environment and API Keys

```bash
cd /Users/liuzihe/Desktop/comp4901b/COMP4901B_Project

# Activate virtual environment
source .venv/bin/activate

# Read DeepSeek-API from .env and export it as OPENAI_API_KEY (used by LLM judge)
export OPENAI_API_KEY=$(grep DeepSeek-API .env | cut -d '=' -f2 | xargs)
```

> Notes:  
> - The Serper-API key for search is automatically read from `.env` (`Serper-API`) inside `src/tools.py`.  
> - Both DeepSeek inference and the LLM judge use `DeepSeek-API`. The line above simply maps it to the `OPENAI_API_KEY` environment variable so that `grade_with_llm_judge.py` can use it.

---

## 1. Generate Predictions: Baseline Model without Search (`nosearch`)

```bash
export PYTHONPATH=.

python scripts/generate_predictions.py \
  --data_path data/nq_test_100.jsonl \
  --output_prediction_path results/predictions_nosearch_v6.jsonl \
  --output_trajectory_path results/trajectories_nosearch_v6.jsonl \
  --setting nosearch \
  --model deepseek-chat \
  --max_workers 4
```

---

## 2. Generate Predictions: Agent with Search (`search`)

```bash
export PYTHONPATH=.

python scripts/generate_predictions.py \
  --data_path data/nq_test_100.jsonl \
  --output_prediction_path results/predictions_search_v6.jsonl \
  --output_trajectory_path results/trajectories_search_v6.jsonl \
  --setting search \
  --model deepseek-chat \
  --max_workers 4
```

---

## 3. (Optional Bonus) Advanced Agent with Browsing (`browsing`)

> This corresponds to the Part I Bonus in the README (adding the browsing tool).  
> Use the following command if you want to run this setting:

```bash
export PYTHONPATH=.

python scripts/generate_predictions.py \
  --data_path data/nq_test_100.jsonl \
  --output_prediction_path results/predictions_browsing_v6.jsonl \
  --output_trajectory_path results/trajectories_browsing_v6.jsonl \
  --setting browsing \
  --model deepseek-chat \
  --max_workers 4
```

---

## 4. EM Evaluation (Exact Match)

### 4.1 EM for `nosearch`

```bash
python scripts/grade_with_em.py \
  --input results/predictions_nosearch_v6.jsonl \
  --output result/grading_results_em.json
```

### 4.2 EM for `search`

```bash
python scripts/grade_with_em.py \
  --input results/predictions_search_v6.jsonl \
  --output result/grading_results_search_em.json
```

### 4.3 (Optional) EM for `browsing`

```bash
python scripts/grade_with_em.py \
  --input results/predictions_browsing_v6.jsonl \
  --output result/grading_results_browsing_v6_em.json
```

---

## 5. LLM Judge Evaluation (DeepSeek as Judge)

> Note: Before running these commands, make sure `OPENAI_API_KEY` is set in Step 0.

### 5.1 LLM Judge for `nosearch`

```bash
  PYTHONPATH=. python scripts/grade_with_llm_judge.py \
    --input results/predictions_nosearch_v6.jsonl \
    --model deepseek-chat \
    --base_url https://api.deepseek.com/v1 \
    --api_key sk-3399321b039a4cb29dca79d2280f3333 \
    --output result/grading_results_llm_judge.json
```

### 5.2 LLM Judge for `search`

```bash
PYTHONPATH=. python scripts/grade_with_llm_judge.py \
    --input results/predictions_search_v6.jsonl \
    --model deepseek-chat \
    --base_url https://api.deepseek.com/v1 \
    --api_key sk-3399321b039a4cb29dca79d2280f3333 \
    --output result/grading_results_serach_llm_judge.json
```

### 5.3 (Optional) LLM Judge for `browsing`

```bash
python scripts/grade_with_llm_judge.py \
  --input results/predictions_browsing_v6.jsonl \
  --model deepseek-chat \
  --base_url https://api.deepseek.com/v1 \
    --api_key sk-3399321b039a4cb29dca79d2280f3333 \
  --output result/grading_results_browsing_v6_llm_judge.json
```

---

## 6. Result Comparison (for Report Writing)

- **Without search (`nosearch`)**:  
  - Check EM in `results/grading_results_nosearch_v6_em.json`.  
  - Check LLM judge accuracy in `results/grading_results_nosearch_v6_llm_judge.json`.

- **With search (`search`)**:  
  - Check EM in `results/grading_results_search_v6_em.json`.  
  - Check LLM judge accuracy in `results/grading_results_search_v6_llm_judge.json`.  

> In the report, you should compare:  
> - EM and LLM judge scores for `nosearch` vs `search`.  
> - Whether you satisfy the README requirements: EM > 36%, LLM judge > 65%, and that `search` improves LLM judge accuracy by at least 5 percentage points compared to `nosearch`.
