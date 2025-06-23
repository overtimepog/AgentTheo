#!/usr/bin/env python3
"""
Agent System Entrypoint
Main entry point for the orchestrated agent system
"""

import os
import sys
import asyncio
from agent.core.main import MainOrchestrator
from agent.utils.logger import setup_logging

async def main():
    """Main async function"""
    # Setup logging
    logger = setup_logging()
    
    # Get task description from environment
    task_description = os.environ.get('TASK_DESCRIPTION')
    
    if not task_description:
        logger.error("No task description provided")
        sys.exit(1)
    
    logger.info(f"Starting orchestrator with task: {task_description}")
    
    try:
        # Initialize and run orchestrator
        orchestrator = MainOrchestrator()
        await orchestrator.initialize()
        result = await orchestrator.execute_task(task_description)        
        logger.info("Task completed successfully")
        logger.info(f"Result: {result}")
        
    except Exception as e:
        logger.error(f"Task failed: {str(e)}", exc_info=True)
        sys.exit(1)
    finally:
        await orchestrator.cleanup()

if __name__ == "__main__":
    asyncio.run(main())