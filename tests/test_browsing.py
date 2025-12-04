#!/usr/bin/env python3
"""
Quick test script for Website Browsing functionality.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tools import browse_website

def main():
    print("Testing Website Browsing...")
    print("-" * 50)
    
    # Test 1: Browse a Wikipedia page
    url = "https://en.wikipedia.org/wiki/Artificial_intelligence"
    print(f"\n1. Browsing URL: {url}")
    
    content = browse_website(url)
    
    if content.startswith("Error"):
        print(f"❌ Error: {content}")
        return
    
    print(f"✓ Successfully extracted content")
    print(f"   Total length: {len(content)} characters")
    
    # Display a snippet of the content
    print("\n--- Content Snippet (First 500 chars) ---")
    print(content[:500] + "...")
    print("-----------------------------------------")
    
    # Test 2: Browse a tech news site (example)
    # Note: Some sites might block scrapers, so this is a best-effort test
    url2 = "https://www.python.org/"
    print(f"\n\n2. Browsing URL: {url2}")
    
    content2 = browse_website(url2)
    
    if content2.startswith("Error"):
        print(f"❌ Error: {content2}")
    else:
        print(f"✓ Successfully extracted content")
        print(f"   Total length: {len(content2)} characters")
        print("\n--- Content Snippet (First 500 chars) ---")
        print(content2[:500] + "...")
        print("-----------------------------------------")
    
    # Test 3: Error Handling
    print("\n\n3. Testing Invalid URL handling...")
    url3 = "https://this-site-does-not-exist-12345.com"
    print(f"   URL: {url3}")
    content3 = browse_website(url3)
    print(f"   Result: {content3}")
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    main()
