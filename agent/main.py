"""
Main Browser Agent implementation using LangGraph
Orchestrates browser automation tasks using LangGraph and Playwright
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, SystemMessage
from .browser_tools import get_browser_toolkit, get_custom_browser_tools
from .openrouter_chat import get_openrouter_chat
from .logger import get_logger

# Load environment variables
load_dotenv('/app/config/.env')

class BrowserAgent:
    """Main browser automation agent using LangGraph"""
    
    def __init__(self):
        self.logger = get_logger('main')
        self.browser = None
        self.toolkit = None
        self.agent = None
        self.checkpointer = MemorySaver()
        
    async def initialize(self):
        """Initialize the agent and browser"""
        self.logger.info("Initializing browser agent with LangGraph...")
        
        # Get browser toolkit
        self.browser, self.toolkit = await get_browser_toolkit()
        
        # Get Chat Model
        llm = get_openrouter_chat()
        
        # Get tools from toolkit
        tools = self.toolkit.get_tools()
        
        # Get custom browser tools with browser instance
        custom_tools = get_custom_browser_tools(self.browser)
        
        # Combine all tools
        all_tools = tools + custom_tools
        
        self.logger.info(f"Loaded {len(tools)} standard tools and {len(custom_tools)} custom tools")
        
        # Create system prompt for the agent
        system_prompt = """You are an intelligent browser automation assistant with advanced DOM analysis capabilities.

        CRITICAL WORKFLOW - FOLLOW THIS EXACT SEQUENCE:
        
        1. **ALWAYS START WITH NAVIGATION**: You MUST use 'navigate_browser' first to go to the target website
           - For Google searches: navigate_browser with URL "https://www.google.com"
           - For other sites: navigate to the appropriate URL
           - NEVER attempt to interact with elements before navigation
           
        2. **VERIFY NAVIGATION**: Use 'current_webpage' to confirm you're on the correct page
        
        3. **ANALYZE THE DOM**: Use 'analyze_dom' to understand the page structure and find correct elements
           - This will provide you with intelligent selectors (IDs, classes, ARIA labels)
           - Use these specific selectors, NOT generic ones like 'input' or 'button'
           
        4. **INTERACT WITH ELEMENTS**: Use the specific selectors from DOM analysis
           - For Google search: Look for selectors like '[name="q"]' or '[title="Search"]'
           - Wait for elements with 'wait_for_element' if needed
           
        5. **HANDLE FAILURES**: If interaction fails, re-analyze DOM as page may have changed

        SEARCH TASK EXAMPLE:
        - Task: "search for AI news on Google"
        - Step 1: navigate_browser to "https://www.google.com"
        - Step 2: analyze_dom to find search input field (usually input[name="q"])
        - Step 3: input_text using the specific selector found (e.g., 'input[name="q"]')
        - Step 4: press_key on the same selector with key="Enter" to submit
           
        GOOGLE SEARCH SPECIFIC TIPS:
        - The search input is typically: input[name="q"] or textarea[name="q"]
        - BEST PRACTICE: Use press_key tool with "Enter" on the search input
        - Example: press_key(selector='input[name="q"]', key='Enter')
        - AVOID clicking search button - it's often hidden or requires waiting
        - The Enter key method is more reliable and mimics user behavior
        
        Available tools:
        - navigate_browser: Navigate to URLs (USE THIS FIRST!)
        - current_webpage: Get current page URL
        - analyze_dom: Comprehensive DOM analysis with intelligent selector generation
        - monitor_dom_events: Monitor page interactions and mutations
        - click_element: Click using JavaScript
        - input_text: Type text with framework compatibility
        - press_key: Press keyboard keys (e.g., Enter to submit forms)
        - wait_for_element: Wait for elements to appear
        - extract_data: Extract information from the page
        - execute_javascript: Run custom JavaScript code
        - take_screenshot: Capture page screenshots for debugging
        
        REMEMBER: The browser starts with a blank page. You MUST navigate first before any interaction!"""
        
        # Define state modifier function to inject system prompt
        def state_modifier(state):
            system_message = {"role": "system", "content": system_prompt}
            return [system_message] + state.get("messages", [])
        
        # Create LangGraph agent with system prompt and configuration
        self.agent = create_react_agent(
            model=llm,
            tools=all_tools,
            checkpointer=self.checkpointer,
            state_modifier=state_modifier  # Apply system prompt function to guide agent behavior
        )
        
        self.logger.info("LangGraph agent initialized successfully")
        
    async def execute_task(self, task_description: str, thread_id: str = "default") -> str:
        """Execute a browser automation task"""
        self.logger.info(f"Executing task: {task_description}")
        
        try:
            # Create configuration with thread ID for conversation persistence
            config = {"configurable": {"thread_id": thread_id}}
            
            # Create user message
            messages = [HumanMessage(content=task_description)]
            
            # Run the agent
            result = await self.agent.ainvoke(
                {"messages": messages},
                config=config
            )
            
            # Extract the final message content
            if result and "messages" in result:
                final_message = result["messages"][-1]
                return final_message.content if hasattr(final_message, 'content') else str(final_message)
            else:
                return "Task completed but no response generated."
                
        except Exception as e:
            self.logger.error(f"Error executing task: {str(e)}")
            raise
            
    async def stream_task(self, task_description: str, thread_id: str = "default"):
        """Execute a task with streaming output"""
        self.logger.info(f"Streaming task execution: {task_description}")
        
        try:
            # Create configuration with thread ID
            config = {"configurable": {"thread_id": thread_id}}
            
            # Create user message
            messages = [HumanMessage(content=task_description)]
            
            # Stream the agent execution
            async for event in self.agent.astream_events(
                {"messages": messages},
                config=config,
                version="v1"
            ):
                yield event
                
        except Exception as e:
            self.logger.error(f"Error streaming task: {str(e)}")
            raise
            
    async def cleanup(self):
        """Cleanup resources"""
        self.logger.info("Cleaning up browser resources...")
        if self.browser:
            try:
                await self.browser.close()
            except:
                pass  # Browser might already be closed
        self.logger.info("Cleanup complete")