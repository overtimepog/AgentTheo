"""
Task execution and orchestration logic
"""

import asyncio
from typing import Dict, Any, List
from ..utils.logger import get_logger

logger = get_logger('task_executor')

class TaskExecutor:
    """Handles task parsing and execution strategies"""
    
    def __init__(self, agent):
        self.agent = agent
        
    async def parse_task(self, task_description: str) -> Dict[str, Any]:
        """Parse natural language task into structured format"""
        logger.info("Parsing task description...")
        
        # Define task patterns
        task_patterns = {
            'navigate': ['go to', 'navigate to', 'open', 'visit'],
            'search': ['search for', 'find', 'look for'],
            'extract': ['extract', 'get', 'scrape', 'collect'],
            'interact': ['click', 'fill', 'submit', 'type', 'enter'],
            'screenshot': ['screenshot', 'capture', 'take picture']
        }
        
        task_type = 'general'
        for action, patterns in task_patterns.items():            
            if any(pattern in task_description.lower() for pattern in patterns):
                task_type = action
                break
                
        return {
            'description': task_description,
            'type': task_type,
            'steps': self._generate_steps(task_type, task_description)
        }
        
    def _generate_steps(self, task_type: str, description: str) -> List[str]:
        """Generate execution steps based on task type"""
        steps = []
        
        if task_type == 'navigate':
            steps.append("Navigate to the specified URL or website")
        elif task_type == 'search':
            steps.append("Navigate to search page")
            steps.append("Enter search query")
            steps.append("Submit search")
            steps.append("Extract results")
        elif task_type == 'extract':
            steps.append("Navigate to target page")
            steps.append("Extract requested information")
            steps.append("Format and return results")
        elif task_type == 'interact':
            steps.append("Navigate to target page")
            steps.append("Find target element")
            steps.append("Perform interaction")
            steps.append("Verify action completed")
            
        return steps
        
    async def execute_with_retry(self, task: str, max_retries: int = 3) -> str:
        """Execute task with retry logic"""
        logger.info(f"Executing task with max {max_retries} retries")
        
        for attempt in range(max_retries):
            try:
                result = await self.agent.execute_task(task)
                logger.info(f"Task completed successfully on attempt {attempt + 1}")
                return result
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise
                    
        return "Task failed after all retry attempts"