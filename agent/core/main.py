"""
Main Browser Agent implementation using LangGraph
Orchestrates browser automation tasks using LangGraph and Playwright
"""

import os
from typing import Dict, Any, Literal
from dotenv import load_dotenv
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
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
        
        # Log the model being used
        self.logger.info(f"Using LLM model: {llm.model_name}")
        self.logger.info(f"Model temperature: {llm.temperature}")
        self.logger.info(f"Max tokens: {llm.max_tokens}")
        
        # Get tools from toolkit
        tools = self.toolkit.get_tools()
        
        # Get custom browser tools with browser instance
        custom_tools = get_custom_browser_tools(self.browser)
        
        # Combine all tools
        all_tools = tools + custom_tools
        
        # Add a special tool for marking task completion
        @tool
        def mark_task_complete(summary: str) -> str:
            """Call this tool ONLY when you have FULLY completed ALL aspects of the user's request.
            
            Args:
                summary: A DETAILED and COMPREHENSIVE summary that must include:
                    - All websites/sources you visited
                    - Key findings from each source
                    - A synthesis of the information gathered
                    - Any relevant insights or patterns
                    
                    Example: "I visited 3 news sources about AI:
                    1. TechCrunch: Found article about OpenAI's new model...
                    2. The Verge: Reported on Google's AI developments...
                    3. Wired: Discussed ethical concerns about AI...
                    Overall, the key trend is..."
            
            Returns:
                Confirmation that the task is complete
            """
            if len(summary) < 100:
                return "Error: Summary too brief. Please provide a detailed summary of all your findings."
            return f"Task completed. Summary: {summary}"
        
        all_tools.append(mark_task_complete)
        
        self.logger.info(f"Loaded {len(tools)} standard tools and {len(custom_tools)} custom tools")
        
        # Create system prompt for the agent
        system_prompt = """You are an intelligent browser automation assistant that MUST complete tasks FULLY and THOROUGHLY.

        CRITICAL INSTRUCTIONS:
        1. You MUST complete ALL aspects of the user's request, not just the first step
        2. For multi-source information gathering (e.g., "find news from multiple sources"):
           - Visit AT LEAST 3-5 different websites
           - Extract FULL article content from each source
           - Provide detailed summaries of each article
        3. ONLY use mark_task_complete when you have FULLY satisfied the user's request
        4. ALWAYS provide detailed results and summaries of what you found/did
        
        For web searches and information gathering:
        1. Navigate to search engines (Google, Bing, DuckDuckGo, etc.)
        2. Search for the requested information
        3. Click on MULTIPLE results (at least 3-5 sources)
        4. Extract FULL article content from each page
        5. Provide comprehensive summaries
        
        Example workflow for "find latest AI news from different sources":
        1. Go to Google and search "latest AI news 2025"
        2. Click on result 1, extract full article
        3. Go back and click on result 2, extract full article
        4. Go back and click on result 3, extract full article
        5. Navigate to another news aggregator (e.g., Hacker News, Reddit)
        6. Find and read more AI news articles
        7. ONLY THEN call mark_task_complete with a comprehensive summary
        
        For Google searches:
        - Navigate to https://www.google.com
        - Use analyze_dom to find the search input
        - Input search terms using input_text
        - Submit using press_key with Enter
        - Click on each result link
        - Extract full content from each page
        
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
        - mark_task_complete: Mark the task as fully complete (ONLY use when done)
        
        Remember: 
        - DO NOT stop after visiting just one source
        - DO NOT provide generic responses  
        - DO extract and read FULL articles
        - DO visit multiple diverse sources
        - ONLY mark complete when ALL requirements are satisfied
        
        IMPORTANT: Continue executing tools until the task is FULLY complete. 
        Do not stop after planning or initial thoughts. Execute all necessary steps.
        
        EXECUTION RULES:
        1. After EACH tool call, decide what to do next
        2. NEVER return empty messages - always say what you're doing
        3. For multi-step tasks, execute ALL steps before marking complete
        4. If a task says "visit multiple sites", you MUST visit at least 3
        5. Always call mark_task_complete at the end with a detailed summary
        
        REACT PATTERN - YOU MUST FOLLOW THIS:
        - After calling navigate_browser → call extract_text to get page content
        - After getting content → decide to navigate to next site OR mark complete
        - NEVER stop after just navigating - always extract and analyze content
        - Continue this loop until you've visited ALL requested sites
        
        CRITICAL: After executing all tools, ALWAYS provide a final summary message 
        describing what you accomplished. Do not end with just tool calls."""
        
        # Define state modifier function to inject system prompt
        def state_modifier(state):
            # Use SystemMessage object instead of dict
            from langchain_core.messages import SystemMessage
            system_message = SystemMessage(content=system_prompt)
            return [system_message] + state.get("messages", [])
        
        # Create LangGraph agent with system prompt and configuration
        self.agent = create_react_agent(
            model=llm,
            tools=all_tools,
            checkpointer=self.checkpointer,
            state_modifier=state_modifier
        )
        
        self.logger.info("LangGraph agent initialized successfully")
        
    async def execute_task(self, task_description: str, thread_id: str = "default") -> str:
        """Execute a browser automation task"""
        self.logger.info(f"Executing task: {task_description}")
        
        try:
            # Create configuration with thread ID and high recursion limit
            config = {
                "configurable": {"thread_id": thread_id},
                "recursion_limit": 100  # Allow many steps for complex tasks
            }
            
            # Enhance the task description to emphasize completion
            enhanced_task = f"""{task_description}
            
            IMPORTANT: This is a multi-step task. You must:
            1. Complete ALL aspects of the request
            2. Visit MULTIPLE sources if gathering information
            3. Extract FULL content, not just snippets
            4. Only call mark_task_complete when FULLY done
            5. Do NOT just plan - EXECUTE the plan
            
            REACT AGENT REMINDER:
            - After EVERY tool response, you MUST decide what to do next
            - DO NOT stop after one tool call
            - Keep calling tools until the task is COMPLETE
            - If you navigated somewhere, extract the content
            - If you extracted content, navigate to the next site
            - Only stop when you've done EVERYTHING requested"""
            
            # Create user message
            messages = [HumanMessage(content=enhanced_task)]
            
            # Log before invoking
            self.logger.info(f"Invoking agent with config: {config}")
            
            # Run the agent to completion
            result = await self.agent.ainvoke(
                {"messages": messages},
                config=config
            )
            
            # Log after invoking
            self.logger.info(f"Agent returned with {len(result.get('messages', []))} messages")
            
            # Extract the final message content
            if result and "messages" in result:
                all_messages = result["messages"]
                
                # Debug: Log all messages
                for i, msg in enumerate(all_messages):
                    msg_type = type(msg).__name__
                    self.logger.debug(f"Message {i} ({msg_type}):")
                    if hasattr(msg, 'content'):
                        self.logger.debug(f"  Content: {msg.content[:100] if msg.content else 'None'}...")
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        self.logger.debug(f"  Tool calls: {[tc.get('name', 'unknown') for tc in msg.tool_calls]}")
                
                # First, check if mark_task_complete was called and extract the summary
                for msg in all_messages:
                    if isinstance(msg, ToolMessage) and hasattr(msg, 'content') and msg.content:
                        if "Task completed. Summary:" in msg.content:
                            # Extract the summary from the tool response
                            summary = msg.content.replace("Task completed. Summary:", "").strip()
                            self.logger.info(f"Task marked as complete with summary: {summary[:100]}...")
                            return summary
                
                # If no completion tool was called, get the last AI message
                self.logger.warning("Task ended without calling mark_task_complete tool")
                
                # Get all AI messages (they contain the actual responses)
                ai_messages = [msg for msg in all_messages if isinstance(msg, AIMessage)]
                
                # Log details about messages for debugging
                self.logger.info(f"Total messages in result: {len(all_messages)}")
                self.logger.info(f"AI messages found: {len(ai_messages)}")
                
                # Check for tool messages
                tool_messages = [msg for msg in all_messages if isinstance(msg, ToolMessage)]
                self.logger.info(f"Tool messages found: {len(tool_messages)}")
                
                if ai_messages:
                    # Find the last AI message with actual content (not just tool calls)
                    planning_count = 0
                    empty_count = 0
                    
                    for msg in reversed(ai_messages):
                        if hasattr(msg, 'content') and msg.content and msg.content.strip():
                            # Skip planning messages
                            content_lower = msg.content.lower()
                            if any(phrase in content_lower for phrase in [
                                "here are the steps", "i will", "let me", "i'll",
                                "i'm going to", "understood", "okay, i will",
                                "search_quality_reflection", "quality_reflection"
                            ]):
                                # This is likely a planning message, skip it
                                planning_count += 1
                                continue
                            # This looks like a real response
                            self.logger.info(f"Found non-planning AI message: {msg.content[:100]}...")
                            return msg.content
                        else:
                            empty_count += 1
                    
                    # If all messages were planning or empty, return a generic completion
                    self.logger.warning(f"All {len(ai_messages)} AI messages were either planning ({planning_count}) or empty ({empty_count})")
                    self.logger.warning("This typically happens when the LLM model doesn't support function calling properly")
                    return "Task completed successfully. The agent performed all requested actions."
                
                return "Task completed but no final summary was provided."
            else:
                return "Task completed but no response generated."
                
        except Exception as e:
            self.logger.error(f"Error executing task: {str(e)}")
            raise
            
    async def stream_task(self, task_description: str, thread_id: str = "default"):
        """Execute a task with streaming output"""
        self.logger.info(f"Streaming task execution: {task_description}")
        
        try:
            # Create configuration with thread ID and high recursion limit
            config = {
                "configurable": {"thread_id": thread_id},
                "recursion_limit": 100
            }
            
            # Enhance the task description
            enhanced_task = f"""{task_description}
            
            IMPORTANT: This is a multi-step task. You must:
            1. Complete ALL aspects of the request
            2. Visit MULTIPLE sources if gathering information
            3. Extract FULL content, not just snippets
            4. Only call mark_task_complete when FULLY done
            5. Do NOT just plan - EXECUTE the plan"""
            
            # Create user message
            messages = [HumanMessage(content=enhanced_task)]
            
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