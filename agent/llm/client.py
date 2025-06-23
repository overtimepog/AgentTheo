"""
OpenRouter LLM client for LangChain integration
"""

import os
from langchain.chat_models.base import BaseChatModel
from langchain.llms.base import LLM
from langchain.callbacks.manager import CallbackManagerForLLMRun
from typing import Optional, List, Any
import httpx
from ..utils.logger import get_logger

logger = get_logger('llm_client')

class OpenRouterLLM(LLM):
    """OpenRouter LLM implementation for LangChain"""
    
    api_key: str
    model: str = "deepseek/deepseek-chat:free"
    temperature: float = 0.7
    max_tokens: int = 2000
    base_url: str = "https://openrouter.ai/api/v1/chat/completions"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.api_key = os.environ.get('OPENROUTER_API_KEY', '')
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is required")
        
        # Override with environment variables if set
        self.model = os.environ.get('LLM_MODEL', self.model)
        self.temperature = float(os.environ.get('LLM_TEMPERATURE', self.temperature))
        self.max_tokens = int(os.environ.get('LLM_MAX_TOKENS', self.max_tokens))
        
    @property
    def _llm_type(self) -> str:
        return "openrouter"
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Call OpenRouter API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/overtimepog/AgentTheo",
            "X-Title": "AgentTheo"
        }
        
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        
        if stop:
            data["stop"] = stop
            
        logger.debug(f"Calling OpenRouter with model: {self.model}")
        
        with httpx.Client() as client:
            response = client.post(
                self.base_url,
                headers=headers,
                json=data,
                timeout=30.0
            )
            response.raise_for_status()
            
        result = response.json()
        return result["choices"][0]["message"]["content"]

def get_llm() -> LLM:
    """Get configured LLM instance"""
    logger.info("Creating OpenRouter LLM client...")
    api_key = os.environ.get('OPENROUTER_API_KEY', '')
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY environment variable is required")
    return OpenRouterLLM(api_key=api_key)