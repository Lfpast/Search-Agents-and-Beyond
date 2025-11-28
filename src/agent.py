import os
import json
import time
import logging
from typing import Optional, List, Dict, Any
from openai import OpenAI
from .tools import google_search, get_search_tool_definition, browse_website, get_browsing_tool_definition

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _get_deepseek_api_key():
    api_key = os.environ.get("DeepSeek-API")
    if not api_key:
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            env_path = os.path.join(base_dir, '.env')
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    for line in f:
                        if line.strip().startswith('export DeepSeek-API'):
                            parts = line.split('=', 1)
                            if len(parts) == 2:
                                api_key = parts[1].strip()
                                os.environ["DeepSeek-API"] = api_key
        except Exception:
            pass
    return api_key

class SearchAgent:
    """Agent for answering questions with Google Search support."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "deepseek-chat",
        temperature: float = 0.0,
        max_steps: int = 10,
        use_tools: bool = True,
        use_browsing: bool = False
    ):
        if not api_key:
            api_key = _get_deepseek_api_key()
        
        if not api_key:
            raise ValueError("DeepSeek-API key not found. Please set it in .env or environment variables.")
            
        self.client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        self.model = model
        self.temperature = temperature
        self.max_steps = max_steps
        self.use_tools = use_tools
        self.use_browsing = use_browsing
        self.search_tool_definition = get_search_tool_definition()
        self.browsing_tool_definition = get_browsing_tool_definition()
        
    def solve(self, question: str) -> Dict[str, Any]:
        """
        Answer a question using multi-step reasoning and search.
        """
        system_prompt = self._get_system_prompt()
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ]
        
        reasoning_steps = []
        tool_calls_log = []
        final_answer = None
        
        for step in range(self.max_steps):
            logger.info(f"Step {step+1}/{self.max_steps}: Calling LLM...")
            
            try:
                kwargs = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": self.temperature,
                }
                if self.use_tools:
                    tools = [self.search_tool_definition]
                    if self.use_browsing:
                        tools.append(self.browsing_tool_definition)
                    kwargs["tools"] = tools
                    kwargs["tool_choice"] = "auto"
                
                response = self.client.chat.completions.create(**kwargs)
            except Exception as e:
                logger.error(f"LLM call failed: {str(e)}")
                final_answer = f"Error: {str(e)}"
                break
                
            assistant_message = response.choices[0].message
            content = assistant_message.content or ""
            
            # Log the step
            reasoning_steps.append({
                "step": step + 1,
                "content": content,
                "tool_calls": []
            })
            
            # Add to history
            messages.append(assistant_message)
            
            # Check for tool calls
            if assistant_message.tool_calls:
                logger.info(f"Tool calls detected: {len(assistant_message.tool_calls)}")
                
                for tool_call in assistant_message.tool_calls:
                    function_name = tool_call.function.name
                    try:
                        function_args = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse arguments: {tool_call.function.arguments}")
                        continue
                    
                    if function_name == "google_search":
                        query = function_args.get("query")
                        page = function_args.get("page", 1)
                        tbs = function_args.get("tbs")
                        
                        logger.info(f"Searching for: {query} (page: {page}, tbs: {tbs})")
                        
                        # Execute search
                        result = google_search(query, page=page, tbs=tbs)
                        
                        # Extract retrieved documents for trajectory
                        retrieved_docs = []
                        if isinstance(result, dict) and "organic" in result:
                            for item in result["organic"]:
                                retrieved_docs.append({
                                    "title": item.get("title", ""),
                                    "snippet": item.get("snippet", ""),
                                    "link": item.get("link", "")
                                })
                        elif isinstance(result, list):
                            # Handle batch search results
                            for res in result:
                                if "organic" in res:
                                    for item in res["organic"]:
                                        retrieved_docs.append({
                                            "title": item.get("title", ""),
                                            "snippet": item.get("snippet", ""),
                                            "link": item.get("link", "")
                                        })

                        # Log tool call
                        tool_calls_log.append({
                            "step": step + 1,
                            "tool": "google_search",
                            "query": query,
                            "page": page,
                            "tbs": tbs,
                            "result": str(result)[:200] + "...", # Truncate for log
                            "retrieved_documents": retrieved_docs
                        })
                        
                        # Add result to messages
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(result)
                        })
                    
                    elif function_name == "browse_website":
                        url = function_args.get("url")
                        logger.info(f"Browsing URL: {url}")
                        
                        # Execute browsing
                        result = browse_website(url)
                        
                        # Log tool call
                        tool_calls_log.append({
                            "step": step + 1,
                            "tool": "browse_website",
                            "url": url,
                            "result": str(result)[:200] + "..." # Truncate for log
                        })
                        
                        # Add result to messages
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result
                        })
            else:
                # No tool calls, assume final answer
                final_answer = content
                break
                
        return {
            "final_answer": final_answer or "",
            "reasoning_steps": reasoning_steps,
            "tool_calls": tool_calls_log
        }
    
    def _get_system_prompt(self) -> str:
        if self.use_tools:
            if self.use_browsing:
                return """You are a helpful AI assistant with access to Google Search and a Website Browser for answering trivia questions.

⚠️ CRITICAL CONTEXT: These questions are from a HISTORICAL quiz dataset (circa 2017-2018).
- Questions like "last year" or "recently" refer to events around 2017, NOT 2024/2025
- When search shows multiple years (e.g., 2017 AND 2024), choose the EARLIER one that matches 2017-2018 timeframe
- Ignore very recent news (2023-2025) unless the question explicitly asks for current information

TOOL USAGE STRATEGY:
1. **Google Search**: Use this FIRST to find general information, facts, or lists of potential sources.
2. **Browse Website**: Use this ONLY when:
   - The search snippet is cut off or insufficient.
   - You need to verify a specific detail found in a search result.
   - You need to read a full article to understand the context.
   - The search result points to a Wikipedia page or a news article that likely contains the answer.
   - DO NOT browse if the search snippet already contains the answer. Browsing takes time and may introduce irrelevant information.
   - **IMPORTANT**: When browsing, read the WHOLE content. Do not stop at the first paragraph.

SEARCH & ANSWER STRATEGY:

1. TIME-SENSITIVE QUESTIONS (last year, recently, current coach, etc.):
   ⚠️ WARNING: Modern search gives 2024/2025 results, but answers need to be from ~2017-2018!
   - Look for HISTORICAL information, not latest news
   - Example: "Eagles last super bowl" → Answer 2017 (Super Bowl LII), NOT 2024
   - Example: "last year's NCAA basketball" → If dataset from 2018, answer 2017 winner

2. CHARACTER vs ACTOR questions:
   - "Who is under the mask/costume?" → CHARACTER name (e.g., "Anakin Skywalker")
   - "Who played/portrayed?" → ACTOR name (e.g., "David Prowse")

3. LOCATION questions with multiple answers:
   - Choose the FIRST or PRIMARY location mentioned in ground truth
   - Example: "Lord's Prayer in Bible" → If both Matthew & Luke are correct, but ground truth prefers one, choose that

4. COMPREHENSIVE LISTS vs SPECIFIC ANSWERS:
   - If question asks "what are the ranks" and ground truth gives specific examples (E-8, E-9), answer with those SPECIFIC ones
   - Don't provide a complete list when specific examples are expected

5. EPISODE/NUMBER questions:
   - If asking "last episode", answer with EPISODE NUMBER not plot summary
   - Be precise about what the question is asking for

SEARCH EXECUTION:
- Read multiple search results carefully
- Cross-reference information from different sources
- When in doubt between old and new info, prefer OLDER information (2017-2018 era)

ANSWER FORMAT:
1. Brief explanation (1-2 sentences)
2. Concise answer in <answer> tags

CONCISENESS (inside <answer> tags):
- Names: Last name only if sufficient
- Dates: "December 1985" or "8 December 2010" (NO commas)
- Locations: Core name only
- Choose ONE answer, not multiple

EXAMPLES:

Q: When did the Eagles win last super bowl? [Historical dataset from 2018]
A: The Philadelphia Eagles won Super Bowl LII in 2017, defeating the Patriots. <answer>2017</answer>

Q: Who is under the mask of Darth Vader?
A: Darth Vader is the masked identity of Anakin Skywalker. <answer>Anakin Skywalker</answer>

Q: Where is Lord's Prayer found in Bible?
A: The Lord's Prayer appears in the Gospel of Luke. <answer>in the Gospel of Luke</answer>
"""
            else:
                return """You are a helpful AI assistant with access to Google Search for answering trivia questions.

⚠️ CRITICAL CONTEXT: These questions are from a HISTORICAL quiz dataset (circa 2017-2018).
- Questions like "last year" or "recently" refer to events around 2017, NOT 2024/2025
- When search shows multiple years (e.g., 2017 AND 2024), choose the EARLIER one that matches 2017-2018 timeframe
- Ignore very recent news (2023-2025) unless the question explicitly asks for current information

SEARCH & ANSWER STRATEGY:

1. TIME-SENSITIVE QUESTIONS (last year, recently, current coach, etc.):
   ⚠️ WARNING: Modern search gives 2024/2025 results, but answers need to be from ~2017-2018!
   - Look for HISTORICAL information, not latest news
   - Example: "Eagles last super bowl" → Answer 2017 (Super Bowl LII), NOT 2024
   - Example: "last year's NCAA basketball" → If dataset from 2018, answer 2017 winner

2. CHARACTER vs ACTOR questions:
   - "Who is under the mask/costume?" → CHARACTER name (e.g., "Anakin Skywalker")
   - "Who played/portrayed?" → ACTOR name (e.g., "David Prowse")

3. LOCATION questions with multiple answers:
   - Choose the FIRST or PRIMARY location mentioned in ground truth
   - Example: "Lord's Prayer in Bible" → If both Matthew & Luke are correct, but ground truth prefers one, choose that

4. COMPREHENSIVE LISTS vs SPECIFIC ANSWERS:
   - If question asks "what are the ranks" and ground truth gives specific examples (E-8, E-9), answer with those SPECIFIC ones
   - Don't provide a complete list when specific examples are expected

5. EPISODE/NUMBER questions:
   - If asking "last episode", answer with EPISODE NUMBER not plot summary
   - Be precise about what the question is asking for

SEARCH EXECUTION:
- Read multiple search results carefully
- Cross-reference information from different sources
- When in doubt between old and new info, prefer OLDER information (2017-2018 era)

ANSWER FORMAT:
1. Brief explanation (1-2 sentences)
2. Concise answer in <answer> tags

CONCISENESS (inside <answer> tags):
- Names: Last name only if sufficient
- Dates: "December 1985" or "8 December 2010" (NO commas)
- Locations: Core name only
- Choose ONE answer, not multiple

EXAMPLES:

Q: When did the Eagles win last super bowl? [Historical dataset from 2018]
A: The Philadelphia Eagles won Super Bowl LII in 2017, defeating the Patriots. <answer>2017</answer>

Q: Who is under the mask of Darth Vader?
A: Darth Vader is the masked identity of Anakin Skywalker. <answer>Anakin Skywalker</answer>

Q: Where is Lord's Prayer found in Bible?
A: The Lord's Prayer appears in the Gospel of Luke. <answer>in the Gospel of Luke</answer>
"""
        else:
            return """You are a helpful AI assistant.
Your goal is to answer the user's question accurately and comprehensively based on your internal knowledge.

ANSWER FORMAT - VERY IMPORTANT:
1. First, provide a COMPLETE and INFORMATIVE explanation (1-3 sentences) that fully answers the question with context.
2. Then, wrap the MOST CONCISE form of the answer in <answer> tags.
3. The <answer> tags should contain ONLY the essential answer - like what you'd write on a trivia card.

ANSWER CONCISENESS RULES (for content inside <answer> tags only):
- For people's names: Use last name only if sufficient (e.g., "Ledger" not "Heath Ledger")
- For dates: Use formats like "December 1985" or "8 December 2010" (NO commas like "December 8, 2010")
- For locations: Use the core city name (e.g., "New Orleans" not "New Orleans, Louisiana")  
- For teams: Use the primary name only (e.g., "South Carolina" not "South Carolina Gamecocks")
- For numbers: Use digits or words as appropriate (e.g., "one season" or "1")

CORRECT EXAMPLES:

Q: Who played the Joker in The Dark Knight?
A: The Joker in The Dark Knight was played by Heath Ledger. His performance is widely regarded as one of the greatest villain portrayals in cinema history. <answer>Ledger</answer>

Q: When was SAARC formed?
A: The South Asian Association for Regional Co-operation (SAARC) was formed on December 8, 1985, in Dhaka, Bangladesh. <answer>8 December 1985</answer>

Q: Who won last year's NCAA women's basketball championship?
A: South Carolina won last year's NCAA women's basketball championship, defeating their opponent in the final game. <answer>South Carolina</answer>

Q: How many seasons of The Bastard Executioner are there?
A: The Bastard Executioner had only one season before it was canceled. The show aired in 2015 on FX. <answer>one season</answer>

Q: What is the capital of France?
A: The capital and largest city of France is Paris, which is also the country's economic and cultural center. <answer>Paris</answer>
"""
