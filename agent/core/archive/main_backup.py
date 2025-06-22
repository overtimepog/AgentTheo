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
from ..tools.browser_tools import get_browser_toolkit, get_custom_browser_tools
from ..llm.openrouter_chat import get_openrouter_chat
from ..utils.logger import get_logger

# Load environment variables
# Try multiple paths for flexibility
if os.path.exists('config/.env'):
    load_dotenv('config/.env')
elif os.path.exists('/app/config/.env'):
    load_dotenv('/app/config/.env')
else:
    load_dotenv()

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
        system_prompt = """You are an intelligent browser automation assistant. Execute tasks step by step.

        IMPORTANT: You must ACTUALLY PERFORM the requested actions, not just describe what you would do.
        
        For web searches and information gathering:
        1. Navigate to the website using navigate_browser
        2. Use analyze_dom to understand the page structure
        3. Input search terms using input_text
        4. Submit searches using press_key with Enter
        5. Click on links using click_element
        6. Extract information using extract_text or extract_data
        7. Continue until you've gathered all requested information
        
        For Google searches specifically:
        - Navigate to https://www.google.com
        - The search input is usually input[name="q"]
        - Use press_key(selector='input[name="q"]', key='Enter') to search
        - Click on search results to visit the actual articles
        - Extract the full content, don't just read snippets
        
        CRITICAL: When asked to gather information from multiple sources:
        - Actually visit each source by clicking links
        - Extract the full article content
        - Summarize what you actually read
        - Don't make up information or provide generic responses
        
        Available tools:
        - navigate_browser: Navigate to URLs
        - current_webpage: Get current URL
        - analyze_dom: Analyze page structure
        - click_element: Click on elements
        - input_text: Type text into inputs
        - press_key: Press keyboard keys
        - wait_for_element: Wait for elements
        - extract_text: Extract all text from page
        - extract_data: Extract structured data
        - take_screenshot: Capture screenshots
        
        Remember: Execute the task completely. Don't just plan - DO IT."""
        
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
            # Create configuration with thread ID and recursion limit
            config = {
                "configurable": {"thread_id": thread_id},
                "recursion_limit": 50
            }
            
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
            # Create configuration with thread ID and recursion limit
            config = {
                "configurable": {"thread_id": thread_id},
                "recursion_limit": 50
            }
            
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