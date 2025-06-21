#!/usr/bin/env python3
"""
Advanced Browser Automation Examples
Demonstrates the enhanced capabilities of the browser agent with custom tools
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment
load_dotenv('config/.env')

from agent.main import BrowserAgent

# Example tasks demonstrating different custom tools
EXAMPLE_TASKS = {
    "text_input": "Go to https://www.google.com and search for 'Playwright browser automation'",
    
    "screenshot": "Navigate to https://example.com and take a full page screenshot",
    
    "form_submission": "Go to https://httpbin.org/forms/post, fill in the custname field with 'Test User', and submit the form",
    
    "wait_and_interact": "Go to https://example.com, wait for the 'More information...' link to be visible, then click it",
    
    "scroll_and_capture": "Navigate to https://en.wikipedia.org/wiki/Web_browser, scroll down 1000 pixels, and take a screenshot",
    
    "hover_interaction": "Go to https://example.com, hover over the 'More information...' link for 3 seconds",
    
    "storage_manipulation": "Go to https://example.com, set a localStorage item 'test_key' with value 'test_value', then retrieve it",
    
    "complex_workflow": """
    Go to https://www.google.com, 
    search for 'LangChain documentation', 
    wait for results to load,
    take a screenshot of the search results,
    then click on the first result
    """
}

async def run_example(task_name: str, task_description: str):
    """Run a single example task"""
    print(f"\n{'='*80}")
    print(f"Example: {task_name}")
    print(f"Task: {task_description}")
    print('='*80)
    
    agent = None
    try:
        # Create and initialize agent
        agent = BrowserAgent()
        await agent.initialize()
        
        # Execute task
        result = await agent.execute_task(task_description)
        print(f"\nResult: {result}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if agent:
            await agent.cleanup()
            
    # Wait a bit between examples
    await asyncio.sleep(2)

async def main():
    """Run all examples or a specific one"""
    import argparse
    parser = argparse.ArgumentParser(description='Advanced Browser Automation Examples')
    parser.add_argument('--task', choices=list(EXAMPLE_TASKS.keys()), 
                        help='Run a specific task example')
    parser.add_argument('--list', action='store_true', 
                        help='List all available examples')
    
    args = parser.parse_args()
    
    if args.list:
        print("\nAvailable Examples:")
        for name, desc in EXAMPLE_TASKS.items():
            print(f"\n{name}:")
            print(f"  {desc[:100]}...")
        return
    
    if args.task:
        # Run specific task
        await run_example(args.task, EXAMPLE_TASKS[args.task])
    else:
        # Run all examples
        print("Running all browser automation examples...")
        for task_name, task_description in EXAMPLE_TASKS.items():
            await run_example(task_name, task_description)

if __name__ == "__main__":
    asyncio.run(main())