"""
Simple DeepAgent using OpenRouter with Streaming

This script creates a basic deep agent that connects to LLMs via OpenRouter.
It reads configuration from a .env file and streams responses.
Tools are automatically registered using the @agent_tool decorator.

Requirements:
    pip install deepagents langchain-openai python-dotenv

.env file should contain:
    THEO_OPENROUTER_API_KEY=your-openrouter-api-key
    THEO_OPENROUTER_MODEL=anthropic/claude-sonnet-4-20250514
"""

import os
from typing import Callable
from dotenv import load_dotenv
from langchain_core.tools import BaseTool, tool as langchain_tool
from langchain_openai import ChatOpenAI
from pydantic import SecretStr
from deepagents import create_deep_agent

# Load environment variables from .env file
load_dotenv()

# =============================================================================
# Tool Registry
# =============================================================================

_tool_registry: list = []


def agent_tool(func: Callable) -> BaseTool:
    """
    Decorator to register a function as an agent tool.
    
    Usage:
        @agent_tool
        def my_tool(param: str) -> str:
            '''Tool description goes here.'''
            return "result"
    """
    # Wrap with LangChain's tool decorator
    wrapped = langchain_tool(func)
    # Add to registry
    _tool_registry.append(wrapped)
    return wrapped


def get_registered_tools() -> list:
    """Get all tools registered with @agent_tool decorator."""
    return _tool_registry.copy()


# =============================================================================
# Define Your Tools Here
# =============================================================================

@agent_tool
def calculator(expression: str) -> str:
    """
    Evaluate a mathematical expression.
    
    Args:
        expression: A mathematical expression like "2 + 2" or "sqrt(16)"
    
    Returns:
        The result of the calculation as a string.
    """
    import math
    # Safe eval with math functions
    allowed = {
        k: v for k, v in math.__dict__.items() 
        if not k.startswith("_")
    }
    allowed.update({"abs": abs, "round": round, "min": min, "max": max})
    try:
        result = eval(expression, {"__builtins__": {}}, allowed)
        return str(result)
    except Exception as e:
        return f"Error: {e}"


@agent_tool
def get_current_time() -> str:
    """
    Get the current date and time.
    
    Returns:
        Current datetime as a formatted string.
    """
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@agent_tool  
def reverse_string(text: str) -> str:
    """
    Reverse a string.
    
    Args:
        text: The string to reverse.
    
    Returns:
        The reversed string.
    """
    return text[::-1]


# =============================================================================
# Agent Setup
# =============================================================================

# Get configuration from environment
api_key = os.getenv("THEO_OPENROUTER_API_KEY")
model_name = os.getenv("THEO_OPENROUTER_MODEL", "anthropic/claude-sonnet-4-20250514")

if not api_key:
    raise ValueError(
        "THEO_OPENROUTER_API_KEY not found in environment. "
        "Please add it to your .env file."
    )

model = ChatOpenAI(
    model=model_name,
    api_key=SecretStr(api_key),
    base_url="https://openrouter.ai/api/v1",
    default_headers={
        "HTTP-Referer": "http://localhost",
    },
    streaming=True,
)

# System prompt for the agent
system_prompt = """You are a helpful AI assistant. You can help with a variety of tasks.

Use your planning capabilities to break down complex tasks into manageable steps.
Use the file system tools to save important information or long content.
Use your custom tools when appropriate.
"""

# Create the deep agent with all registered tools
agent = create_deep_agent(
    model=model,
    system_prompt=system_prompt,
    tools=get_registered_tools(),  # Automatically includes all @agent_tool functions
)


# =============================================================================
# Chat Interface
# =============================================================================

def stream_chat(message: str):
    """Stream a response from the agent."""
    for chunk in agent.stream(
        {"messages": [{"role": "user", "content": message}]},
        stream_mode="messages",
    ):
        msg, metadata = chunk
        
        msg_type = getattr(msg, "type", None)
        msg_content = getattr(msg, "content", None)

        if msg_type == "AIMessageChunk" and msg_content:
            if isinstance(msg_content, str):
                print(msg_content, end="", flush=True)
            elif isinstance(msg_content, list):
                for item in msg_content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        print(item.get("text", ""), end="", flush=True)
                    elif isinstance(item, str):
                        print(item, end="", flush=True)
        elif isinstance(msg, str):
            print(msg, end="", flush=True)


def main():
    print(f"🚀 DeepAgent started with model: {model_name}")
    print(f"📦 Loaded {len(get_registered_tools())} custom tools: {[t.name for t in get_registered_tools()]}")
    print("Type 'quit' or 'exit' to stop.\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ("quit", "exit"):
                print("Goodbye!")
                break
            
            print("\nAgent: ", end="", flush=True)
            stream_chat(user_input)
            print("\n")
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}\n")


if __name__ == "__main__":
    main()