"""
Agent Setup and Configuration

This module handles the creation and configuration of the DeepAgent,
including model setup and the chat interface.
"""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from pydantic import SecretStr
from deepagents import create_deep_agent

# Import tools package to trigger auto-discovery
from src import tools  # noqa: F401
from src.registry import get_registered_tools

# Load environment variables from .env file
load_dotenv()

# =============================================================================
# Agent Setup
# =============================================================================

def create_agent():
    """Create and configure the DeepAgent with all registered tools."""
    
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
        tools=get_registered_tools(),
    )
    
    return agent, model_name


# =============================================================================
# Chat Interface
# =============================================================================

def stream_chat(agent, message: str):
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


def run_chat_loop():
    """Run the main chat loop."""
    agent, model_name = create_agent()
    tools = get_registered_tools()
    
    print(f"🚀 DeepAgent started with model: {model_name}")
    print(f"📦 Loaded {len(tools)} custom tools: {[t.name for t in tools]}")
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
            stream_chat(agent, user_input)
            print("\n")
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}\n")
