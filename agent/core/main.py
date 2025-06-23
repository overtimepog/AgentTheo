"""
Main Orchestrator Agent for AgentTheo
Analyzes tasks and delegates to specialized agents as needed
"""

import os
import asyncio
from typing import Dict, Any, Optional, AsyncGenerator, Union, List
from enum import Enum
from dotenv import load_dotenv
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.tools import tool
from ..llm.openrouter_chat import get_openrouter_chat
from ..utils.logger import get_logger
from ..browser.agent import BrowserAgent

# Load environment variables
if os.path.exists('config/.env'):
    load_dotenv('config/.env')
elif os.path.exists('/app/config/.env'):
    load_dotenv('/app/config/.env')
else:
    load_dotenv()


class TaskType(Enum):
    """Types of tasks the orchestrator can identify"""
    GENERAL_QUESTION = "general_question"
    WEB_AUTOMATION = "web_automation"
    CALCULATION = "calculation"
    EXPLANATION = "explanation"
    UNKNOWN = "unknown"


class MainOrchestrator:
    """Main orchestrator that analyzes tasks and delegates to specialized agents"""
    
    def __init__(self):
        self.logger = get_logger('orchestrator')
        self.agent = None
        self.checkpointer = MemorySaver()
        self._browser_agent: Optional[BrowserAgent] = None
        self._is_initialized = False
        
    async def initialize(self):
        """Initialize the orchestrator agent"""
        if self._is_initialized:
            self.logger.info("Orchestrator already initialized")
            return
            
        self.logger.info("Initializing main orchestrator...")
        
        # Get Chat Model
        llm = get_openrouter_chat()
        
        self.logger.info(f"Using LLM model: {llm.model_name}")
        
        # Create tools for the orchestrator
        all_tools = []
        
        # Tool to analyze task type
        @tool
        def analyze_task(task_description: str) -> str:
            """Analyze the task to determine what type of agent or action is needed.
            
            Args:
                task_description: The user's task description
                
            Returns:
                Analysis of the task type and requirements
            """
            task_lower = task_description.lower()
            
            # Keywords that indicate web automation is needed
            web_keywords = [
                'navigate', 'browse', 'website', 'url', 'search online', 
                'find on the web', 'extract from', 'click', 'screenshot',
                'google', 'search for', 'web page', 'online'
            ]
            
            # Keywords for general questions
            general_keywords = [
                'what is', 'explain', 'how does', 'why', 'when',
                'who', 'define', 'describe', 'tell me about'
            ]
            
            # Check for web automation needs
            if any(keyword in task_lower for keyword in web_keywords):
                return "WEB_AUTOMATION: This task requires browser automation to interact with web pages."
            
            # Check for calculations
            if any(op in task_lower for op in ['+', '-', '*', '/', 'calculate', 'compute', 'math']):
                return "CALCULATION: This is a mathematical calculation task."
            
            # Check for general questions
            if any(keyword in task_lower for keyword in general_keywords) and \
               not any(keyword in task_lower for keyword in web_keywords):
                return "GENERAL_QUESTION: This is a general question that can be answered without web access."
            
            return "UNKNOWN: Task type unclear, may need further analysis."
        
        all_tools.append(analyze_task)
        
        # Tool to delegate to browser agent
        @tool
        async def delegate_to_browser(task_description: str) -> str:
            """Delegate a task to the browser automation agent.
            
            Args:
                task_description: The task to delegate to the browser agent
                
            Returns:
                Result from the browser agent
            """
            try:
                self.logger.info("Delegating task to browser agent...")
                
                # Create browser agent if not exists
                if self._browser_agent is None:
                    self.logger.info("Creating new browser agent instance...")
                    self._browser_agent = BrowserAgent()
                    await self._browser_agent.initialize()
                
                # Execute the task
                result = await self._browser_agent.execute_task(task_description)
                
                # Clean up browser agent after task
                self.logger.info("Task completed, cleaning up browser agent...")
                await self._browser_agent.cleanup()
                self._browser_agent = None
                
                return result
                
            except Exception as e:
                self.logger.error(f"Error in browser delegation: {e}")
                # Ensure cleanup on error
                if self._browser_agent:
                    try:
                        await self._browser_agent.cleanup()
                    except:
                        pass
                    self._browser_agent = None
                return f"Error executing browser task: {str(e)}"
        
        all_tools.append(delegate_to_browser)
        
        # Tool for direct responses
        @tool
        def provide_answer(answer: str) -> str:
            """Provide a direct answer to the user's question.
            
            Args:
                answer: The answer to provide
                
            Returns:
                The formatted answer
            """
            return answer
        
        all_tools.append(provide_answer)
        
        # System prompt for the orchestrator
        system_prompt = """You are AgentTheo, an intelligent assistant that orchestrates various specialized agents.

        YOUR ROLE:
        1. Analyze incoming tasks to determine what type of assistance is needed
        2. Delegate to specialized agents when necessary (e.g., BrowserAgent for web tasks)
        3. Provide direct answers for simple questions that don't require specialized tools
        
        TASK ANALYSIS RULES:
        1. Use analyze_task to understand what the user is asking for
        2. For tasks requiring web interaction (browsing, searching online, extracting web content):
           - Use delegate_to_browser to hand off to the browser agent
        3. For general questions, calculations, or explanations that don't need web access:
           - Use provide_answer to respond directly
        
        IMPORTANT:
        - Only delegate to browser agent when web interaction is actually needed
        - The browser agent will handle all web automation and return results
        - You coordinate and ensure the user gets comprehensive answers
        - Be efficient - don't create agents unnecessarily
        
        WORKFLOW:
        1. Receive user task
        2. Analyze what type of task it is
        3. Either:
           a) Delegate to browser agent for web tasks
           b) Answer directly for non-web tasks
        4. Return the result to the user"""
        
        # Define state modifier
        def state_modifier(state):
            from langchain_core.messages import SystemMessage
            system_message = SystemMessage(content=system_prompt)
            return [system_message] + state.get("messages", [])
        
        # Create the orchestrator agent
        self.agent = create_react_agent(
            model=llm,
            tools=all_tools,
            checkpointer=self.checkpointer,
            state_modifier=state_modifier
        )
        
        self.logger.info("Main orchestrator initialized successfully")
        self._is_initialized = True
    
    async def execute_task(self, task_description: str, thread_id: str = "orchestrator") -> str:
        """Execute a task by analyzing and delegating as needed"""
        self.logger.info(f"Orchestrator received task: {task_description}")
        
        try:
            config = {
                "configurable": {"thread_id": thread_id},
                "recursion_limit": 50
            }
            
            # Create the task message
            messages = [HumanMessage(content=task_description)]
            
            # Run the orchestrator
            result = await self.agent.ainvoke(
                {"messages": messages},
                config=config
            )
            
            # Extract the final response
            if result and "messages" in result:
                for msg in reversed(result["messages"]):
                    if isinstance(msg, AIMessage) and msg.content:
                        # Skip tool-calling messages
                        if hasattr(msg, 'tool_calls') and msg.tool_calls:
                            continue
                        return msg.content
            
            return "Task completed but no response generated."
            
        except Exception as e:
            self.logger.error(f"Error executing orchestrated task: {e}")
            return f"Error: {str(e)}"
    
    async def astream(
        self,
        command: str,
        stream_mode: Union[str, List[str]] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream responses from the orchestrator"""
        
        self.logger.info(f"Orchestrator streaming task: {command[:50]}...")
        
        if not self.agent:
            yield {
                "type": "error",
                "content": "Orchestrator not initialized"
            }
            return
        
        # Default config
        if config is None:
            config = {
                "configurable": {"thread_id": "orchestrator-stream"},
                "recursion_limit": 50
            }
        
        try:
            # Yield start event
            yield {
                "type": "start",
                "content": "🤔 Analyzing your request...",
                "metadata": {"agent": "orchestrator"}
            }
            
            # Small delay for UI
            await asyncio.sleep(0.5)
            
            # Create input
            input_data = {
                "messages": [HumanMessage(content=command)]
            }
            
            # Execute the task
            result = await self.agent.ainvoke(input_data, config=config)
            
            # Check if browser delegation occurred
            browser_used = False
            if result and "messages" in result:
                for msg in result["messages"]:
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        for tc in msg.tool_calls:
                            if tc.get('name') == 'delegate_to_browser':
                                browser_used = True
                                yield {
                                    "type": "status",
                                    "content": "🌐 Browser agent handling web automation...",
                                    "metadata": {"agent": "browser"}
                                }
                                break
            
            # Extract and stream the final response
            final_content = ""
            if result and "messages" in result:
                for msg in reversed(result["messages"]):
                    if isinstance(msg, AIMessage) and msg.content:
                        if hasattr(msg, 'tool_calls') and msg.tool_calls:
                            continue
                        final_content = msg.content
                        break
            
            # Stream the response
            if final_content:
                words = final_content.split()
                for i, word in enumerate(words):
                    yield {
                        "type": "token",
                        "content": word + " ",
                        "metadata": {"count": i + 1}
                    }
                    await asyncio.sleep(0.02)
            
            yield {
                "type": "complete",
                "content": "Done",
                "metadata": {"browser_used": browser_used}
            }
            
        except Exception as e:
            self.logger.error(f"Streaming error: {str(e)}", exc_info=True)
            yield {
                "type": "error",
                "content": f"Error: {str(e)}"
            }
    
    async def cleanup(self):
        """Cleanup any active agents"""
        self.logger.info("Cleaning up orchestrator resources...")
        
        # Clean up browser agent if active
        if self._browser_agent:
            try:
                await self._browser_agent.cleanup()
                self._browser_agent = None
            except Exception as e:
                self.logger.error(f"Error cleaning up browser agent: {e}")
        
        self.logger.info("Orchestrator cleanup complete")