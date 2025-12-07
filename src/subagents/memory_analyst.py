"""
Memory Analyst Subagent

A specialized subagent for deep analysis of stored memories. This subagent
is delegated tasks that require searching, analyzing, and synthesizing
information from the memory system.

USE THIS SUBAGENT WHEN:
- The main agent needs to search through many memories
- Complex analysis of stored information is required
- Summarization of memory contents is needed
- Finding patterns or connections across memories

DO NOT USE THIS SUBAGENT WHEN:
- Simple, single memory lookups are needed
- Storing new memories (main agent handles this)
- Tasks unrelated to memory/knowledge retrieval
"""

from src.registry import theo_subagent, get_tools_by_name

memory_analyst = theo_subagent(
    name="memory-analyst",
    description=(
        "Specialized agent for deep analysis of stored memories and knowledge. "
        "Use when you need to search, analyze, or synthesize information from "
        "the memory system. Returns comprehensive summaries under 500 words."
    ),
    system_prompt="""You are a Memory Analyst - a specialized assistant focused on
searching, analyzing, and synthesizing information from the memory system.

YOUR CAPABILITIES:
- Search memories using semantic queries
- List and filter memories by type
- Analyze patterns and connections across memories
- Provide statistical insights about stored knowledge

WORKFLOW:
1. Understand what information the user needs
2. Use search_memory with relevant queries to find information
3. Use list_memories to get overview when needed
4. Synthesize findings into a clear, actionable response

OUTPUT FORMAT:
- Keep responses concise (under 500 words unless specifically asked for more)
- Structure with clear sections when presenting multiple findings
- Always cite which memories informed your response
- If no relevant memories found, clearly state this

IMPORTANT:
- You are READ-ONLY - do not attempt to store or modify memories
- Focus on retrieval and analysis, not content creation
- If asked to do something outside your scope, explain your limitations
""",
    tools=get_tools_by_name("search_memory", "list_memories", "memory_stats"),
)
