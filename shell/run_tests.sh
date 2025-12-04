#!/bin/bash

# Get the project root directory (assuming script is in shell/ folder)
# Resolves to /home/jackson/COMP_4901B/Project
PROJECT_ROOT="$(dirname "$(dirname "$(readlink -f "$0")")")"
cd "$PROJECT_ROOT"

echo "========================================"
echo "       Running All Project Tests        "
echo "========================================"
echo "Project Root: $PROJECT_ROOT"
echo ""

# Function to run a test script
run_test() {
    test_script=$1
    echo "▶ Running $test_script..."
    if [ -f "$test_script" ]; then
        python3 "$test_script"
        exit_code=$?
        if [ $exit_code -eq 0 ]; then
            echo "✅ $test_script completed successfully."
        else
            echo "❌ $test_script failed with exit code $exit_code."
        fi
    else
        echo "⚠️  Test file not found: $test_script"
    fi
    echo "----------------------------------------"
    echo ""
}

# List of tests to run
run_test "tests/test_maps.py"
run_test "tests/test_scholar.py"
run_test "tests/test_shopping.py"
run_test "tests/test_browsing.py"

echo "========================================"
echo "          All Tests Completed           "
echo "========================================"
