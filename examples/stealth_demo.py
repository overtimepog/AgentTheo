#!/usr/bin/env python3
"""
Demonstrate stealth browser automation
Shows how to use the browser with stealth features enabled
"""

import asyncio
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.browser.agent import BrowserAgent


async def search_google_with_stealth():
    """Example: Search Google without triggering CAPTCHA"""
    print("Initializing browser agent with stealth features...")
    
    # Create agent
    agent = BrowserAgent()
    await agent.initialize()
    
    print("\nAgent initialized. Performing Google search...")
    
    # Search task
    task = """
    Navigate to Google and search for "latest AI news 2025". 
    Extract the titles of the first 5 search results.
    Take a screenshot of the results page.
    """
    
    try:
        result = await agent.execute_task(task)
        print(f"\nSearch completed! Result:\n{result}")
    except Exception as e:
        print(f"\nError during search: {e}")
    finally:
        await agent.cleanup()


async def test_multiple_sites():
    """Example: Visit multiple sites that typically use anti-bot measures"""
    print("Testing stealth on multiple websites...")
    
    agent = BrowserAgent()
    await agent.initialize()
    
    sites_to_test = [
        "https://www.google.com",
        "https://www.amazon.com",
        "https://www.linkedin.com",
        "https://www.indeed.com"
    ]
    
    for site in sites_to_test:
        print(f"\nTesting {site}...")
        task = f"""
        Navigate to {site} and check if the page loads normally.
        Look for any CAPTCHA challenges or "unusual traffic" messages.
        Take a screenshot of the page.
        Report what you see.
        """
        
        try:
            result = await agent.execute_task(task, thread_id=site)
            print(f"Result for {site}: {result[:200]}...")
        except Exception as e:
            print(f"Error on {site}: {e}")
    
    await agent.cleanup()


async def interactive_browsing():
    """Example: Interactive browsing session with stealth"""
    print("Starting interactive browsing session...")
    
    agent = BrowserAgent()
    await agent.initialize()
    
    print("\nAgent ready. You can now give browsing commands.")
    print("Type 'exit' to quit.\n")
    
    while True:
        command = input("Enter command (or 'exit'): ")
        if command.lower() == 'exit':
            break
            
        try:
            result = await agent.execute_task(command)
            print(f"\nResult: {result}\n")
        except Exception as e:
            print(f"\nError: {e}\n")
    
    await agent.cleanup()
    print("Session ended.")


async def main():
    """Run stealth demonstrations"""
    print("=== Browser Stealth Demonstration ===\n")
    print("This demo shows how the stealth features prevent CAPTCHA detection.\n")
    
    print("1. Google Search Test")
    print("2. Multiple Sites Test")
    print("3. Interactive Browsing")
    print("4. Exit")
    
    choice = input("\nSelect demo (1-4): ")
    
    if choice == "1":
        await search_google_with_stealth()
    elif choice == "2":
        await test_multiple_sites()
    elif choice == "3":
        await interactive_browsing()
    else:
        print("Exiting...")


if __name__ == "__main__":
    # Ensure we have API key
    if not os.environ.get('OPENROUTER_API_KEY'):
        print("Error: OPENROUTER_API_KEY not set in environment")
        print("Please set it in config/.env or export it")
        sys.exit(1)
    
    asyncio.run(main())