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
from .browser_tools import get_browser_toolkit
from .browser_tools import get_custom_browser_tools
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
        system_prompt = """You are a helpful browser automation assistant. 
        You have access to various browser automation tools to help users interact with web pages.
        When given a task, break it down into steps and use the appropriate tools to complete it.
        Always be clear about what actions you're taking and report the results."""
        
        # Create LangGraph agent
        self.agent = create_react_agent(
            model=llm,
            tools=all_tools,
            checkpointer=self.checkpointer,
            prompt=SystemMessage(content=system_prompt)
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