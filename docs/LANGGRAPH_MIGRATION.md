# LangGraph Migration Guide

## Overview

This document outlines the migration from LangChain agents to LangGraph for the Browser Agent project. LangGraph provides a more flexible, graph-based approach to building agents with better support for persistence, streaming, and complex workflows.

## Key Changes

### 1. Dependencies

Added `langgraph==0.2.60` to `requirements.txt`

### 2. Agent Initialization

**Before (LangChain):**
```python
from langchain.agents import AgentType, initialize_agent
from langchain.memory import ConversationBufferMemory

self.memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True
)

self.agent = initialize_agent(
    tools=all_tools,
    llm=llm,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    memory=self.memory,
    handle_parsing_errors=True,
    max_iterations=10
)
```

**After (LangGraph):**
```python
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

self.checkpointer = MemorySaver()

self.agent = create_react_agent(
    model=llm,
    tools=all_tools,
    prompt=system_prompt,
    checkpointer=self.checkpointer
)
```

### 3. Task Execution

**Before:**
```python
result = await self.agent.arun(task_description)
```

**After:**
```python
config = {"configurable": {"thread_id": thread_id}}
messages = [HumanMessage(content=task_description)]

result = await self.agent.ainvoke(
    {"messages": messages},
    config=config
)
```

### 4. New Features

#### Streaming Support
```python
async def stream_task(self, task_description: str, thread_id: str = "default"):
    config = {"configurable": {"thread_id": thread_id}}
    messages = [HumanMessage(content=task_description)]
    
    async for event in self.agent.astream_events(
        {"messages": messages},
        config=config,
        version="v1"
    ):
        yield event
```

#### Thread-Based Conversation Memory
- Each conversation can have its own `thread_id`
- State is automatically persisted between calls
- Enables multi-turn conversations with context retention

## Benefits

1. **Better Architecture**: Graph-based approach is more flexible than chains
2. **Native Streaming**: Built-in support for streaming responses
3. **Persistence**: Automatic state persistence with checkpointers
4. **Human-in-the-Loop**: Better support for interactive workflows
5. **Debugging**: Improved visibility into agent execution flow

## Tool Compatibility

All existing browser tools (both standard Playwright tools and custom tools) remain compatible with LangGraph without modification, as they inherit from `BaseTool`.

## Testing

### Basic Test
```python
agent = BrowserAgent()
await agent.initialize()
result = await agent.execute_task("go to google and search for AI news")
```

### Streaming Test
```python
async for event in agent.stream_task("navigate to example.com"):
    print(event)
```

### Conversation Memory Test
```python
# First message
result1 = await agent.execute_task(
    "go to example.com", 
    thread_id="conversation_1"
)

# Follow-up using same thread
result2 = await agent.execute_task(
    "what was the title?", 
    thread_id="conversation_1"
)
```

## Migration Checklist

- [x] Update requirements.txt with langgraph
- [x] Replace initialize_agent with create_react_agent
- [x] Update task execution to use messages format
- [x] Add streaming support
- [x] Implement thread-based memory
- [x] Maintain backward compatibility
- [x] Test with existing browser tools
- [x] Update documentation

## Backward Compatibility

The migration maintains backward compatibility:
- `execute_task` method signature is preserved (with optional thread_id)
- All existing tools work without modification
- Docker setup remains unchanged
- Test scripts continue to work

## Future Enhancements

With LangGraph, we can now implement:
1. Multi-agent workflows
2. Complex decision trees
3. Human approval steps
4. Better error recovery with graph-based retry logic
5. Visual debugging of agent execution paths