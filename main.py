"""
Simple DeepAgent using OpenRouter with Streaming

This script creates a basic deep agent that connects to LLMs via OpenRouter.
It reads configuration from a .env file and streams responses.

Requirements:
    pip install deepagents langchain-openai python-dotenv

.env file should contain:
    THEO_OPENROUTER_API_KEY=your-openrouter-api-key
    THEO_OPENROUTER_MODEL=anthropic/claude-sonnet-4-20250514
"""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from deepagents import create_deep_agent
from pydantic import SecretStr

# Load environment variables from .env file
load_dotenv()

# Get configuration from environment
api_key = os.getenv("THEO_OPENROUTER_API_KEY")
model_name = os.getenv("THEO_OPENROUTER_MODEL", "anthropic/claude-sonnet-4-20250514")

if not api_key:
    raise ValueError(
        "THEO_OPENROUTER_API_KEY not found in environment. "
        "Please add it to your .env file."
    )

# Create OpenRouter-compatible model using ChatOpenAI
model = ChatOpenAI(
    api_key=SecretStr(api_key),
    base_url="https://openrouter.ai/api/v1",
    default_headers={
        "HTTP-Referer": "http://localhost",  # Required by OpenRouter
    },
    streaming=True,  # Enable streaming
)

# System prompt for the agent
system_prompt = """You are a helpful AI assistant. You can help with a variety of tasks.

Use your planning capabilities to break down complex tasks into manageable steps.
Use the file system tools to save important information or long content.
"""

# Create the deep agent
agent = create_deep_agent(
    model=model,
    system_prompt=system_prompt,
)


def stream_chat(message: str):
    """Stream a response from the agent."""
    for chunk in agent.stream(
        {"messages": [{"role": "user", "content": message}]},
        stream_mode="messages",
    ):
        # chunk is a tuple of (message_chunk, metadata)
        msg, metadata = chunk
        
        # Only print content from AI messages (not tool calls/results)
        if isinstance(msg, str):
            print(msg, end="", flush=True)
            continue

        message_type = getattr(msg, "type", None)
        content = getattr(msg, "content", None)

        if isinstance(msg, dict):
            message_type = msg.get("type", message_type)
            content = msg.get("content", content)

        if message_type == "AIMessageChunk" and content:
            # Handle string content
            if isinstance(content, str):
                print(content, end="", flush=True)
            # Handle list content (some models return list of dicts)
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        print(item.get("text", ""), end="", flush=True)
                    elif isinstance(item, str):
                        print(item, end="", flush=True)
            elif isinstance(content, dict) and content.get("type") == "text":
                print(content.get("text", ""), end="", flush=True)


def main():
    print(f"🚀 DeepAgent started with model: {model_name}")
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