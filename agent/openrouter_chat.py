"""
OpenRouter Chat Model implementation for LangChain with tool support
"""

import os
from typing import List, Optional, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import BaseTool
from .logger import get_logger

logger = get_logger('openrouter_chat')


class OpenRouterChat(ChatOpenAI):
    """OpenRouter ChatModel implementation that supports tool binding"""
    
    def __init__(self, **kwargs):
        # Set OpenRouter specific defaults
        kwargs['openai_api_base'] = kwargs.get('openai_api_base', 'https://openrouter.ai/api/v1')
        kwargs['openai_api_key'] = kwargs.get('openai_api_key', os.environ.get('OPENROUTER_API_KEY', ''))
        
        # Set model from environment or use default
        kwargs['model_name'] = kwargs.get('model_name', os.environ.get('LLM_MODEL', 'deepseek/deepseek-chat'))
        kwargs['temperature'] = kwargs.get('temperature', float(os.environ.get('LLM_TEMPERATURE', '0.7')))
        kwargs['max_tokens'] = kwargs.get('max_tokens', int(os.environ.get('LLM_MAX_TOKENS', '2000')))
        
        # Add OpenRouter specific headers
        kwargs['model_kwargs'] = kwargs.get('model_kwargs', {})
        kwargs['default_headers'] = {
            "HTTP-Referer": "https://github.com/browser-agent",
            "X-Title": "Browser Agent"
        }
        
        super().__init__(**kwargs)
        logger.info(f"Initialized OpenRouter Chat with model: {self.model_name}")
        
    def bind_tools(self, tools: List[BaseTool], **kwargs) -> BaseChatModel:
        """Bind tools to the model for tool-calling support"""
        # OpenRouter models may not all support function calling
        # For models that do support it, this will work
        # For models that don't, we may need to use a different approach
        logger.info(f"Binding {len(tools)} tools to OpenRouter model")
        return super().bind_tools(tools, **kwargs)


def get_openrouter_chat() -> BaseChatModel:
    """Get configured OpenRouter ChatModel instance"""
    logger.info("Creating OpenRouter Chat client...")
    
    api_key = os.environ.get('OPENROUTER_API_KEY', '')
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY environment variable is required")
    
    # Check if the model supports function calling
    model = os.environ.get('LLM_MODEL', 'deepseek/deepseek-chat')
    
    # Models that support function calling
    function_calling_models = [
        'openai/gpt-4',
        'openai/gpt-4-turbo',
        'openai/gpt-3.5-turbo',
        'anthropic/claude-3',
        'anthropic/claude-2',
        'google/gemini-pro'
    ]
    
    # Log a warning if using a model that might not support function calling
    if not any(model.startswith(prefix) for prefix in function_calling_models):
        logger.warning(f"Model '{model}' may not support function calling. Consider using a model that supports tools.")
    
    return OpenRouterChat()