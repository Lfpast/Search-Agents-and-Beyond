#!/usr/bin/env python3
"""
Quick test script for Google Scholar functionality.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tools import google_scholar

def main():
    print("Testing Google Scholar Search...")
    print("-" * 50)
    
    # Test 1: Search for machine learning papers
    print("\n1. Searching for 'transformer neural network' papers (2017-2024)...")
    result = google_scholar(
        query="transformer neural network",
        num=5,
        year_low=2017,
        year_high=2024
    )
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        print("\nMake sure your Serper-API key is set in .env file:")
        print("Serper-API=your_api_key_here")
        return
    
    print(f"✓ Found {len(result['papers'])} papers")
    
    # Display results
    for i, paper in enumerate(result['papers'], 1):
        print(f"\n  {i}. {paper['title']}")
        print(f"     👥 Authors: {', '.join(paper['authors']) if paper['authors'] else 'N/A'}")
        print(f"     📅 Year: {paper['year']}")
        print(f"     🔗 Link: {paper['link']}")
        print(f"     📄 Cited by: {paper['cited_by']}")
        if paper['pdf_link']:
            print(f"     📥 PDF: {paper['pdf_link']}")
    
    # Test 2: Search for Climate Change (Recent)
    print("\n" + "-" * 30)
    print("\n2. Searching for 'climate change impact' (2023-2024)...")
    result2 = google_scholar(
        query="climate change impact",
        num=3,
        year_low=2023
    )
    
    if "error" in result2:
        print(f"❌ Error: {result2['error']}")
    else:
        print(f"✓ Found {len(result2['papers'])} papers")
        for i, paper in enumerate(result2['papers'], 1):
            print(f"\n  {i}. {paper['title']}")
            print(f"     📅 Year: {paper['year']}")
            print(f"     📄 Cited by: {paper['cited_by']}")
            print(f"     🔗 Link: {paper['link']}")
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    main()
