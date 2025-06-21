#!/usr/bin/env python3
"""
Browser Agent Entrypoint
Main entry point for the containerized browser automation agent
"""

import os
import sys
import asyncio
import logging
from agent.main import BrowserAgent
from agent.logger import setup_logging

async def main():
    """Main async function"""
    # Setup logging
    logger = setup_logging()
    
    # Get task description from environment
    task_description = os.environ.get('TASK_DESCRIPTION')
    
    if not task_description:
        logger.error("No task description provided")
        sys.exit(1)
    
    logger.info(f"Starting browser agent with task: {task_description}")
    
    try:
        # Initialize and run agent
        agent = BrowserAgent()
        await agent.initialize()
        result = await agent.execute_task(task_description)        
        logger.info("Task completed successfully")
        logger.info(f"Result: {result}")
        
    except Exception as e:
        logger.error(f"Task failed: {str(e)}", exc_info=True)
        sys.exit(1)
    finally:
        await agent.cleanup()

if __name__ == "__main__":
    asyncio.run(main())