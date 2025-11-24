import requests
import json
import os
from typing import Dict, Any, List, Union

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
