import requests
import json
import os
import re
from typing import Dict, Any, List, Union
from bs4 import BeautifulSoup

def _get_api_key():
    api_key = os.environ.get("Serper-API")
    if not api_key:
        # Fallback: try to read from .env in parent directory
        try:
            # Go up one level from src to Project
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            env_path = os.path.join(base_dir, '.env')
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    for line in f:
                        if line.strip().startswith('export Serper-API'):
                            parts = line.split('=', 1)
                            if len(parts) == 2:
                                api_key = parts[1].strip()
                                # Also set it in environ for future use
                                os.environ["Serper-API"] = api_key
        except Exception:
            pass
    return api_key

def google_search(query: Union[str, List[str]], page: int = 1, tbs: str = None) -> Dict[str, Any]:
    """
    Perform a Google search using the Serper API.
    
    Args:
        query: The search query string or list of strings.
        page: Page number (default 1).
        tbs: Time range parameter (e.g., 'qdr:h' for past hour).
        
    Returns:
        Dict: The search results.
    """
    api_key = _get_api_key()
    
    if not api_key:
        return {"error": "Serper-API key not found. Please set it in .env or environment variables."}

    url = "https://google.serper.dev/search"
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }

    # Map user-friendly tbs values to Serper/Google format if needed
    # But we will expose the friendly names in the tool definition and map them here
    tbs_mapping = {
        "past_hour": "qdr:h",
        "past_24h": "qdr:d",
        "past_week": "qdr:w",
        "past_month": "qdr:m",
        "past_year": "qdr:y"
    }
    
    final_tbs = tbs_mapping.get(tbs, tbs) if tbs else None

    if isinstance(query, list):
        # Batch search
        payload_list = []
        for q in query:
            item = {"q": q, "gl": "hk", "page": page}
            if final_tbs:
                item["tbs"] = final_tbs
            payload_list.append(item)
        payload = json.dumps(payload_list)
    else:
        # Single search
        data = {
            "q": query,
            "gl": "hk",
            "page": page
        }
        if final_tbs:
            data["tbs"] = final_tbs
        payload = json.dumps(data)

    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": f"Search failed: {str(e)}"}

def get_search_tool_definition() -> Dict[str, Any]:
    """
    Get the tool definition for OpenAI function calling format.
    """
    return {
        "type": "function",
        "function": {
            "name": "google_search",
            "description": "Search Google for information. Use this to find facts, current events, or specific details needed to answer the user's question.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": ["string", "array"],
                        "items": {
                            "type": "string"
                        },
                        "description": "The search query string, or a list of query strings for batch search."
                    },
                    "page": {
                        "type": "integer",
                        "description": "The page number of search results to retrieve (default is 1). Increase this to see more results.",
                        "default": 1
                    },
                    "tbs": {
                        "type": "string",
                        "enum": ["anytime", "past_hour", "past_24h", "past_week", "past_month", "past_year"],
                        "description": "Time range for the search results. Default is 'anytime'. Use 'past_24h' for very recent news.",
                        "default": "anytime"
                    }
                },
                "required": ["query"]
            }
        }
    }

def browse_website(url: str) -> str:
    """
    Browse a website and extract its text content.
    
    Args:
        url: The URL of the website to browse.
        
    Returns:
        str: The extracted text content of the website.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 1. Remove junk elements
        # Expanded list of non-content tags
        for element in soup(["script", "style", "meta", "noscript", "header", "footer", "nav", "aside", "iframe", "svg", "symbol", "form", "button", "input"]):
            element.extract()
            
        # 2. Try to narrow down to main content
        # Many sites use <main> or <article> or specific IDs/classes
        content_element = soup.find('main') or soup.find('article')
        
        # If not found, try common class names (simple heuristic)
        if not content_element:
            # Look for divs with 'content' or 'main' in id or class
            # We use a simple list check to avoid complex regex if possible, but regex is cleaner
            for tag in soup.find_all('div'):
                id_val = tag.get('id', '')
                class_val = tag.get('class', [])
                if isinstance(class_val, list):
                    class_val = ' '.join(class_val)
                
                if 'content' in str(id_val).lower() or 'main' in str(id_val).lower() or \
                   'content' in str(class_val).lower() or 'main' in str(class_val).lower():
                    # Heuristic: Main content usually has significant text length
                    if len(tag.get_text()) > 200: 
                        content_element = tag
                        break
        
        # Fallback to body or root
        target = content_element if content_element else soup
        
        # 3. Extract text with separator to keep structure
        # separator='\n' helps distinguish headers and paragraphs
        text = target.get_text(separator='\n', strip=True)
        
        # 4. Clean up whitespace
        # Collapse multiple newlines into two (paragraph break)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # 5. Truncate if too long to avoid context window issues
        # DeepSeek has 131072 token limit, reserve ~120k tokens for safety
        # Rough estimate: 1 token ≈ 4 characters, so ~480k characters
        max_chars = 131072
        if len(text) > max_chars:
            text = text[:max_chars] + "... (content truncated due to context length limit)"
            
        return text
        
    except Exception as e:
        return f"Error browsing website: {str(e)}"

def get_browsing_tool_definition() -> Dict[str, Any]:
    """
    Get the tool definition for the browsing tool.
    """
    return {
        "type": "function",
        "function": {
            "name": "browse_website",
            "description": "Browse a website URL to read its full content. Use this when search results are not detailed enough or when you need to verify specific information from a source.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL of the website to browse."
                    }
                },
                "required": ["url"]
            }
        }
    }
