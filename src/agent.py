import os
import json
import time
import logging
from typing import Optional, List, Dict, Any
from openai import OpenAI
from .tools import google_search, get_search_tool_definition

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
        use_tools: bool = True
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
        self.tool_definition = get_search_tool_definition()
        
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
                    kwargs["tools"] = [self.tool_definition]
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
            else:
                # No tool calls, assume final answer
                final_answer = content
                break
                
        return {
            "final_answer": final_answer,
            "reasoning_steps": reasoning_steps,
            "tool_calls": tool_calls_log
        }
    
    def _get_system_prompt(self) -> str:
        if self.use_tools:
            return """You are a helpful AI assistant with access to Google Search.
Your goal is to answer the user's question accurately and comprehensively.

Process:
1. Analyze the user's question.
2. If you need external information to answer, use the 'google_search' tool.
3. You can perform multiple searches if needed. If the first page of results doesn't contain the answer, try searching again with 'page' set to 2, 3, etc.
4. Use the 'tbs' parameter to filter results by time (e.g., 'past_24h') for recent news or time-sensitive questions.
5. Synthesize the information found to provide a clear answer.
6. If you have enough information, provide the final answer directly without calling tools.

IMPORTANT: When you provide the final answer, you MUST wrap the concise answer phrase in <answer> tags.
For example:
The capital of France is <answer>Paris</answer>.
The date of the event was <answer>December 14, 1972</answer>.
"""
        else:
            return """You are a helpful AI assistant.
Your goal is to answer the user's question accurately and comprehensively based on your internal knowledge.
IMPORTANT: When you provide the final answer, you MUST wrap the concise answer phrase in <answer> tags.
For example:
The capital of France is <answer>Paris</answer>.
The date of the event was <answer>December 14, 1972</answer>.
"""
