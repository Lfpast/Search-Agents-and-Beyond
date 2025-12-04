#!/usr/bin/env python3
"""
Quick test script for Google Shopping functionality.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tools import google_shopping

def main():
    print("Testing Google Shopping Search...")
    print("-" * 50)
    
    # Test 1: Search for products
    print("\n1. Searching for 'Nike Air Max 97' in Hong Kong...")
    result = google_shopping(
        query="Nike Air Max 97",
        num=5,
        page=1
    )
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        print("\nMake sure your Serper-API key is set in .env file:")
        print("Serper-API=your_api_key_here")
        return
    
    # Check if 'shopping' key exists in result
    items = result.get('shopping', [])
    print(f"✓ Found {len(items)} items")
    
    # Display results
    for i, item in enumerate(items, 1):
        print(f"\n  {i}. {item.get('title', 'No Title')}")
        print(f"     💰 Price: {item.get('price', 'N/A')}")
        print(f"     🏪 Source: {item.get('source', 'N/A')}")
        print(f"     ⭐ Rating: {item.get('rating', 'N/A')} ({item.get('ratingCount', 0)} reviews)")
        print(f"     🔗 Link: {item.get('link', 'N/A')}")
    
    # Test 2: Electronics
    print("\n" + "-" * 30)
    print("\n2. Searching for 'Sony WH-1000XM5' (Electronics)...")
    result2 = google_shopping(
        query="Sony WH-1000XM5",
        num=3,
        page=1
    )
    
    if "error" in result2:
        print(f"❌ Error: {result2['error']}")
    else:
        items2 = result2.get('shopping', [])
        print(f"✓ Found {len(items2)} items")
        for i, item in enumerate(items2, 1):
            print(f"\n  {i}. {item.get('title', 'No Title')}")
            print(f"     💰 Price: {item.get('price', 'N/A')}")
            print(f"     🏪 Source: {item.get('source', 'N/A')}")
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    main()
