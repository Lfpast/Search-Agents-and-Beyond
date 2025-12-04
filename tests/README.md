# Tests Directory

This directory contains test scripts for the project.

## Test Files

### `test_maps.py`
Quick test script for Google Maps functionality.

**Usage:**
```bash
python3 tests/test_maps.py
```

**What it does:**
1. Searches for coffee shops in Central, Hong Kong
2. Displays detailed information about the results
3. Creates an interactive map visualization in `tests/test_coffee_map.html`

### `test_scholar.py`
Quick test script for Google Scholar functionality.

**Usage:**
```bash
python3 tests/test_scholar.py
```

**What it does:**
1. Searches for academic papers related to "transformer neural network"
2. Filters results by year (2017-2024)
3. Displays paper titles, authors, citations, and PDF links

### `test_shopping.py`
Quick test script for Google Shopping functionality.

**Usage:**
```bash
python3 tests/test_shopping.py
```

**What it does:**
1. Searches for "Nike Air Max 97" in Hong Kong
2. Displays product titles, prices, sources, and ratings

### `test_browsing.py`
Quick test script for Website Browsing functionality.

**Usage:**
```bash
python3 tests/test_browsing.py
```

**What it does:**
1. Browses a Wikipedia page and extracts content
2. Browses a tech website (python.org) and extracts content
3. Displays content snippets and total character count

**Expected output:**
- Console output with search results or extracted content
- For maps, an HTML map file in the `tests/` directory

## Running Tests

Make sure you have:
1. API keys configured in `.env` file
2. All dependencies installed: `pip install -r requirements.txt`
3. Run from the project root directory

## Adding New Tests

When adding new test files:
1. Follow the naming convention: `test_*.py`
2. Add proper imports and path setup
3. Save all output files to the `examples/` directory
4. Include clear print statements for test progress
5. Update this README with test description

