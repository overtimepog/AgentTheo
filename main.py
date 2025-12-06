"""
Simple DeepAgent using OpenRouter with Streaming

This script is the entry point for the DeepAgent application.
Tools are automatically discovered from the src/tools/ directory.

To add new tools:
    1. Create a new .py file in src/tools/
    2. Import and use the @agent_tool decorator:
    
        from src.registry import agent_tool
        
        @agent_tool
        def my_tool(param: str) -> str:
            '''Tool description goes here.'''
            return "result"

Requirements:
    pip install deepagents langchain-openai python-dotenv

.env file should contain:
    THEO_OPENROUTER_API_KEY=your-openrouter-api-key
    THEO_OPENROUTER_MODEL=anthropic/claude-sonnet-4-20250514
"""

from src.agent import run_chat_loop


def main():
    """Entry point for the DeepAgent application."""
    run_chat_loop()


if __name__ == "__main__":
    main()