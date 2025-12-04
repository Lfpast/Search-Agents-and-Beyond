import requests
import json
import os
import re
import math
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
                        line = line.strip()
                        # Support "Serper-API=xxx", "export Serper-API=xxx", and spaces around =
                        # Normalize line: remove 'export ' and strip whitespace
                        clean_line = line.replace('export ', '').strip()
                        if clean_line.startswith('Serper-API'):
                            parts = clean_line.split('=', 1)
                            if len(parts) == 2:
                                api_key = parts[1].strip()
                                # Also set it in environ for future use
                                os.environ["Serper-API"] = api_key
                                break
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

def google_shopping(query: str, num: int = 10, page: int = 1) -> Dict[str, Any]:
    """
    Perform a Google Shopping search using the Serper API.
    Results are localized to Hong Kong (gl='hk').
    
    Args:
        query: The search query string.
        num: Number of results to return (default 10).
        page: Page number (default 1).
        
    Returns:
        Dict: The shopping search results.
    """
    api_key = _get_api_key()
    
    if not api_key:
        return {"error": "Serper-API key not found. Please set it in .env or environment variables."}

    url = "https://google.serper.dev/shopping"
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }

    payload = json.dumps({
        "q": query,
        "gl": "hk",
        "num": num,
        "page": page
    })

    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": f"Shopping search failed: {str(e)}"}

def get_shopping_tool_definition() -> Dict[str, Any]:
    """
    Get the tool definition for the shopping tool.
    """
    return {
        "type": "function",
        "function": {
            "name": "google_shopping",
            "description": "Search Google Shopping for product information, prices, and availability in Hong Kong.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The product search query."
                    },
                    "num": {
                        "type": "integer",
                        "description": "Number of results to return (default 10).",
                        "default": 10
                    },
                    "page": {
                        "type": "integer",
                        "description": "The page number of results (default 1).",
                        "default": 1
                    }
                },
                "required": ["query"]
            }
        }
    }


def google_maps_search(query: str, location: str = None, num: int = 10) -> Dict[str, Any]:
    """
    Search for places using Google Maps via Serper API.
    
    Args:
        query: The search query (e.g., "coffee shops", "restaurants").
        location: The location to search around (e.g., "Central, Hong Kong").
        num: Number of results to return (default 10).
        
    Returns:
        Dict: The places search results with standardized format.
    """
    api_key = _get_api_key()
    
    if not api_key:
        return {"error": "Serper-API key not found. Please set it in .env or environment variables."}

    url = "https://google.serper.dev/places"
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }

    # Combine query with location if provided
    search_query = f"{query} in {location}" if location else query
    
    payload = json.dumps({
        "q": search_query,
        "gl": "hk",
        "num": num
    })

    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        response.raise_for_status()
        raw_result = response.json()
        
        # Standardize the response format
        places = []
        if "places" in raw_result:
            for place in raw_result["places"]:
                standardized_place = {
                    "title": place.get("title", ""),
                    "address": place.get("address", ""),
                    "rating": place.get("rating", 0),
                    "reviews": place.get("ratingCount", 0),  # Serper uses ratingCount
                    "price_level": place.get("priceLevel", ""),
                    "category": place.get("category", ""),
                    "phone": place.get("phoneNumber", ""),
                    "website": place.get("website", ""),
                    "latitude": place.get("latitude"),
                    "longitude": place.get("longitude"),
                    "cid": place.get("cid", ""),
                    "position": place.get("position", 0),
                    # Generate Google Maps link from cid for user convenience
                    "google_maps_link": f"https://www.google.com/maps?cid={place.get('cid', '')}" if place.get("cid") else ""
                }
                places.append(standardized_place)
        
        return {
            "query": search_query,
            "places": places,
            "total": len(places)
        }
        
    except Exception as e:
        return {"error": f"Maps search failed: {str(e)}"}


def recommend_places(places: List[Dict], top_n: int = 5, price_preference: str = "any") -> Dict[str, Any]:
    """
    Recommend places based on a comprehensive scoring algorithm.
    
    The algorithm considers:
    - Rating (40% weight): Higher rating = better
    - Reviews count (30% weight): More reviews = more reliable
    - Search position (30% weight): Higher position in Google results = more relevant
    
    Args:
        places: List of place dictionaries from google_maps_search.
        top_n: Number of top recommendations to return (default 5).
        price_preference: Price filter - "budget" ($), "moderate" ($$), "expensive" ($$$), or "any".
        
    Returns:
        Dict: Recommended places with scores and explanations.
    """
    if not places:
        return {"error": "No places provided for recommendation."}
    
    # Price level mapping for filtering
    price_map = {
        "budget": ["$", "$1–50", "HK$1–50", "$1-50"],
        "moderate": ["$$", "$50–100", "HK$50–100", "$50-100", "$50–150", "HK$50–150"],
        "expensive": ["$$$", "$100+", "HK$100+", "$150+", "$$$$"]
    }
    
    # Filter by price preference if specified
    filtered_places = places
    if price_preference != "any" and price_preference in price_map:
        filtered_places = [
            p for p in places 
            if any(level in str(p.get("price_level", "")) for level in price_map[price_preference])
        ]
        # If no matches, use all places
        if not filtered_places:
            filtered_places = places
    
    # Calculate max reviews for normalization
    max_reviews = max((p.get("reviews", 0) for p in filtered_places), default=1)
    if max_reviews == 0:
        max_reviews = 1
    
    # Calculate scores for each place
    scored_places = []
    for place in filtered_places:
        rating = place.get("rating", 0) or 0
        reviews = place.get("reviews", 0) or 0
        position = place.get("position", 10) or 10
        
        # Scoring formula:
        # - Rating score (0-40): rating / 5.0 * 40
        # - Reviews score (0-30): log-normalized reviews * 30
        # - Position score (0-30): inverse position * 30
        
        rating_score = (rating / 5.0) * 40
        
        # Log-normalize reviews (prevents one place with massive reviews from dominating)
        reviews_score = (math.log10(reviews + 1) / math.log10(max_reviews + 1)) * 30
        
        # Position score (position 1 = 30 points, position 10 = 3 points)
        position_score = (1 / position) * 30
        
        total_score = rating_score + reviews_score + position_score
        
        scored_places.append({
            **place,
            "recommendation_score": round(total_score, 2),
            "score_breakdown": {
                "rating_score": round(rating_score, 2),
                "reviews_score": round(reviews_score, 2),
                "position_score": round(position_score, 2)
            }
        })
    
    # Sort by score descending
    scored_places.sort(key=lambda x: x["recommendation_score"], reverse=True)
    
    # Get top N recommendations
    top_recommendations = scored_places[:top_n]
    
    return {
        "recommendations": top_recommendations,
        "total_analyzed": len(filtered_places),
        "price_filter": price_preference,
        "algorithm": "Weighted score: Rating(40%) + Reviews(30%) + Position(30%)"
    }


def create_map_visualization(places: List[Dict], output_file: str = "map.html") -> Dict[str, Any]:
    """
    Create a simple HTML map visualization using Leaflet.js.
    
    Args:
        places: List of place dictionaries.
        output_file: Path to save the HTML file.
        
    Returns:
        Dict: Result with file path and number of markers.
    """
    try:
        if not places:
            return {"error": "No places to visualize"}
            
        # Calculate center
        lats = [p.get("latitude") for p in places if p.get("latitude")]
        lngs = [p.get("longitude") for p in places if p.get("longitude")]
        
        if not lats or not lngs:
            return {"error": "No valid coordinates found in places"}
            
        center_lat = sum(lats) / len(lats)
        center_lng = sum(lngs) / len(lngs)
        
        # Create markers JS
        markers_js = ""
        for p in places:
            lat = p.get("latitude")
            lng = p.get("longitude")
            if lat and lng:
                title = p.get("title", "Unknown").replace("'", "\\'")
                address = p.get("address", "").replace("'", "\\'")
                rating = p.get("rating", "N/A")
                
                popup_content = f"<b>{title}</b><br>{address}<br>Rating: {rating}⭐"
                markers_js += f"L.marker([{lat}, {lng}]).addTo(map).bindPopup('{popup_content}');\\n"

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Map Visualization</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
    <style>
        body {{ margin: 0; padding: 0; }}
        #map {{ width: 100%; height: 100vh; }}
    </style>
</head>
<body>
    <div id="map"></div>
    <script>
        var map = L.map('map').setView([{center_lat}, {center_lng}], 13);
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }}).addTo(map);
        
        {markers_js}
    </script>
</body>
</html>
        """
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)
            
        return {
            "file": output_file,
            "num_markers": len(lats)
        }
        
    except Exception as e:
        return {"error": f"Failed to create map: {str(e)}"}


def get_maps_tool_definition() -> Dict[str, Any]:
    """
    Get the tool definition for the Google Maps search tool.
    """
    return {
        "type": "function",
        "function": {
            "name": "google_maps_search",
            "description": "Search for places on Google Maps. Use this to find restaurants, cafes, attractions, stores, or any other places in a specific location.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The type of place to search for (e.g., 'coffee shops', 'Italian restaurants', 'tourist attractions')."
                    },
                    "location": {
                        "type": "string",
                        "description": "The location to search around (e.g., 'Central, Hong Kong', 'Tsim Sha Tsui')."
                    },
                    "num": {
                        "type": "integer",
                        "description": "Number of results to return (default 10).",
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        }
    }


def get_recommend_places_tool_definition() -> Dict[str, Any]:
    """
    Get the tool definition for the place recommendation tool.
    """
    return {
        "type": "function",
        "function": {
            "name": "recommend_places",
            "description": "Get smart recommendations from place search results. Uses a scoring algorithm based on rating, reviews, and search position to find the best places.",
            "parameters": {
                "type": "object",
                "properties": {
                    "top_n": {
                        "type": "integer",
                        "description": "Number of top recommendations to return (default 5).",
                        "default": 5
                    },
                    "price_preference": {
                        "type": "string",
                        "enum": ["any", "budget", "moderate", "expensive"],
                        "description": "Price preference filter: 'budget' ($), 'moderate' ($$), 'expensive' ($$$), or 'any'.",
                        "default": "any"
                    }
                },
                "required": []
            }
        }
    }


def google_scholar(query: str, num: int = 10, year_low: int = None, year_high: int = None) -> Dict[str, Any]:
    """
    Search for academic papers using Google Scholar via Serper API.
    
    Args:
        query: The search query string (e.g., "machine learning", "transformer neural network").
        num: Number of results to return (default 10).
        year_low: Filter papers published after this year (inclusive).
        year_high: Filter papers published before this year (inclusive).
        
    Returns:
        Dict: The scholar search results with papers information.
    """
    api_key = _get_api_key()
    
    if not api_key:
        return {"error": "Serper-API key not found. Please set it in .env or environment variables."}

    url = "https://google.serper.dev/scholar"
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }

    payload_data = {
        "q": query,
        "num": num
    }
    
    # Add year filters if provided
    if year_low:
        payload_data["as_ylo"] = year_low
    if year_high:
        payload_data["as_yhi"] = year_high

    payload = json.dumps(payload_data)

    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        response.raise_for_status()
        raw_result = response.json()
        
        # Standardize the response format
        papers = []
        if "organic" in raw_result:
            for paper in raw_result["organic"]:
                # Parse publication info to extract authors
                pub_info = paper.get("publicationInfo", "")
                authors = []
                if pub_info and " - " in pub_info:
                    # Format is typically: "Author1, Author2 - Journal, Year - Publisher"
                    author_part = pub_info.split(" - ")[0]
                    authors = [a.strip() for a in author_part.split(",") if a.strip()]
                
                standardized_paper = {
                    "title": paper.get("title", ""),
                    "link": paper.get("link", ""),
                    "snippet": paper.get("snippet", ""),
                    "publication_info": pub_info,
                    "authors": authors,
                    "year": paper.get("year", ""),
                    "cited_by": paper.get("citedBy", 0),
                    "pdf_link": paper.get("pdfUrl", "") or paper.get("htmlUrl", "")
                }
                papers.append(standardized_paper)
        
        return {
            "query": query,
            "papers": papers,
            "total": len(papers)
        }
        
    except Exception as e:
        return {"error": f"Scholar search failed: {str(e)}"}


def get_scholar_tool_definition() -> Dict[str, Any]:
    """
    Get the tool definition for the Google Scholar search tool.
    """
    return {
        "type": "function",
        "function": {
            "name": "google_scholar",
            "description": "Search for academic papers, research articles, and citations on Google Scholar. Use this for literature review, finding research papers, or academic information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The academic search query (e.g., 'deep learning image classification', 'transformer attention mechanism')."
                    },
                    "num": {
                        "type": "integer",
                        "description": "Number of results to return (default 10).",
                        "default": 10
                    },
                    "year_low": {
                        "type": "integer",
                        "description": "Filter papers published after this year (e.g., 2020 for papers from 2020 onwards)."
                    },
                    "year_high": {
                        "type": "integer",
                        "description": "Filter papers published before this year (e.g., 2023 for papers up to 2023)."
                    }
                },
                "required": ["query"]
            }
        }
    }
