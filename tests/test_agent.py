#!/usr/bin/env python3
"""
Basic tests for Browser Agent
"""

import asyncio
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.browser.agent import BrowserAgent
from agent.browser.tools.browser_tools import get_browser_toolkit
from agent.llm.client import get_llm

async def test_browser_creation():
    """Test browser creation"""
    print("Testing browser creation...")
    browser, toolkit = await get_browser_toolkit()
    assert browser is not None
    assert toolkit is not None
    await browser.close()
    print("✓ Browser creation successful")

async def test_llm_client():
    """Test LLM client"""
    print("Testing LLM client...")
    try:
        llm = get_llm()
        assert llm is not None
        print("✓ LLM client created successfully")
    except ValueError as e:
        print(f"✗ LLM client error: {e}")
        print("  Make sure OPENROUTER_API_KEY is set in config/.env")

async def test_agent_initialization():
    """Test agent initialization"""
    print("Testing agent initialization...")
    try:
        agent = BrowserAgent()
        await agent.initialize()
        print("✓ Agent initialized successfully")
        await agent.cleanup()
    except Exception as e:
        print(f"✗ Agent initialization error: {e}")

async def main():
    """Run all tests"""
    print("Running Browser Agent tests...\n")
    
    await test_browser_creation()
    await test_llm_client()
    await test_agent_initialization()
    
    print("\nTests completed!")

if __name__ == "__main__":
    # Set test environment
    os.environ['LOG_LEVEL'] = 'WARNING'
    
    asyncio.run(main())