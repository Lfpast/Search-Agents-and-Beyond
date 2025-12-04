# Multi-Tool AI Agent

This project implements a sophisticated AI agent capable of using multiple external tools (Google Search, Shopping, Maps, Scholar, and Web Browsing) to solve complex user queries. The agent utilizes a ReAct (Reasoning + Acting) loop to plan, execute, and refine its actions.

## 📂 Project Structure

The repository is organized as follows:

```text
COMP4901B_Project/
├── src/
│   ├── agent.py .................... Core Agent logic (ReAct loop, prompt engineering)
│   ├── tools.py .................... Implementation of all 5 tools (Search, Maps, Shopping, etc.)
│   └── metrics.py .................. Evaluation metrics for agent performance
├── tests/
│   ├── test_maps.py ................ Unit tests for Google Maps & Visualization
│   ├── test_scholar.py ............. Unit tests for Google Scholar search
│   ├── test_shopping.py ............ Unit tests for Google Shopping (HK localized)
│   ├── test_browsing.py ............ Unit tests for Website Browsing & Content Extraction
│   └── README.md ................... Specific documentation for the test suite
├── shell/
│   ├── run_tests.sh ................ ⚡ Script to run all unit tests
│   ├── run_experiment.sh ........... 🧪 Script for full training/evaluation pipeline
│   └── find_improvements.sh ........ 📈 Script to analyze performance gains
├── scripts/
│   ├── generate_predictions.py ..... Generates agent trajectories & answers
│   ├── grade_with_em.py ............ Exact Match (EM) grading logic
│   └── grade_with_llm_judge.py ..... LLM-based evaluation logic
├── docs/
│   ├── TOOL_USER_GUIDE.md .......... 📘 COMPLETE GUIDE for using all agent tools
│   └── part2_realistic_tasks.md .... 🌍 Real-world task demonstrations & trajectories
├── data/
│   └── nq_test_100.jsonl ........... Natural Questions dataset for evaluation
├── results/ ........................ Directory for storing evaluation outputs
├── requirements.txt ................ Python dependencies
└── README.md ....................... This file
```

## 🚀 Quick Start

### 1. Environment Setup
Ensure you have your API keys ready (DeepSeek & Serper).

```bash
# 1. Clone the repository
git clone <repo_url>
cd COMP4901B_Project

# 2. Create .env file
touch .env
# Add your keys:
# Serper-API=your_key_here
# DeepSeek-API=your_key_here

# 3. Install dependencies
pip install -r requirements.txt
```

## 🤖 Automated Workflows (Shell Scripts)

We have automated the entire development, testing, and evaluation lifecycle using shell scripts located in the `shell/` directory.

### 1. Verify Tool Functionality (`run_tests.sh`)
Before running experiments, ensure all external tools (Maps, Scholar, Shopping, etc.) are working correctly.

```bash
./shell/run_tests.sh
```
*   **What it does**: Sequentially runs unit tests for all tools in `tests/`.
*   **When to use**: After setting up the environment or modifying `src/tools.py`.

### 2. Run Full Experiment Pipeline (`run_experiment.sh`)
This script automates the generation and evaluation process for different agent configurations (e.g., No Search vs. Search vs. Browsing).

```bash
./shell/run_experiment.sh
```
*   **What it does**:
    1.  Generates predictions using `scripts/generate_predictions.py`.
    2.  Evaluates results using Exact Match (`scripts/grade_with_em.py`).
    3.  Evaluates results using LLM Judge (`scripts/grade_with_llm_judge.py`).
*   **Output**: Results are saved in `results/v6/` (configurable in the script).

### 3. Analyze Improvements (`find_improvements.sh`)
After running experiments, use this script to compare different runs and identify where the agent improved.

```bash
./shell/find_improvements.sh
```
*   **What it does**: Compares the grading results of two different settings (e.g., `nosearch` vs `search`) to highlight fixed cases.
*   **Configuration**: You may need to update the file paths inside the script to point to your specific result files.

## 🐍 Helper Scripts (`scripts/`)

The `scripts/` directory contains the Python logic used by the shell scripts for batch processing and evaluation.

*   **`generate_predictions.py`**: The main driver for running the agent on the dataset. It takes the NQ dataset, runs the agent for each question (with specified tools enabled), and saves the trajectories and final answers.
*   **`grade_with_em.py`**: Calculates the **Exact Match (EM)** score by comparing the agent's prediction against the ground truth short answers.
*   **`grade_with_llm_judge.py`**: Uses an LLM (DeepSeek/GPT) to evaluate the correctness of the agent's answer, providing a more nuanced score than simple string matching.

## 📚 Documentation

We provide comprehensive documentation to help you understand the agent's capabilities and real-world applications.

### 1. Tool User Guide
👉 **[docs/TOOL_USER_GUIDE.md](docs/TOOL_USER_GUIDE.md)**
*   Detailed API reference for all 5 tools.
*   Parameter explanations and code examples.
*   Response formats for Search, Shopping, Maps, Scholar, and Browsing.

### 2. Realistic Tasks & Trajectories
👉 **[docs/part2_realistic_tasks.md](docs/part2_realistic_tasks.md)**
*   Demonstrates **3 complex real-world scenarios** (Café Search, Headphone Shopping, Literature Review).
*   Compares manual workflows vs. automated agent trajectories.
*   Analyzes the agent's reasoning steps and tool usage patterns.

## ©License
This project is for academic use only.
