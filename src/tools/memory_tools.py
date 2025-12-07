"""
Memory Tools

Agent-accessible tools for interacting with the semantic memory system.
These tools allow the agent to store, search, and manage memories.
"""

import json
import logging

from src.registry import theo_tool
from src.memory import get_memory_manager, MEMORY_TYPES, MemoryManagerError

logger = logging.getLogger(__name__)


@theo_tool
def store_memory(
    content: str,
    memory_type: str = "general",
    metadata: str = "{}",
) -> str:
    """
    Store information in semantic memory for long-term retrieval across conversations.

    USE THIS TOOL WHEN:
    - User shares personal preferences, facts about themselves, or important context
    - User explicitly says "remember this" or "don't forget"
    - You learn something important that should persist beyond this conversation
    - Saving results from research or tool outputs for future reference
    - Examples: "I'm allergic to peanuts", "My project uses React", "Remember I prefer dark mode"

    DO NOT USE THIS TOOL WHEN:
    - Information is only relevant to the current conversation
    - User is just making casual conversation, not sharing persistent info
    - The information is already stored (use search_memory to check first)
    - Storing trivial or obvious information

    Args:
        content: The text content to store. Be concise but complete.
        memory_type: Category - "general" (preferences/facts), "document" (reference material),
                    "conversation" (chat context), "tool_output" (saved results)
        metadata: Optional JSON string with extra context like {"category": "health", "priority": "high"}

    Returns:
        Confirmation with memory ID, or error message.

    Examples:
        store_memory("User is allergic to peanuts", "general", '{"category": "health"}')
        store_memory("Project uses Python 3.13 and FastAPI", "document", '{"topic": "tech-stack"}')
    """
    try:
        # Parse metadata JSON
        try:
            custom_metadata = json.loads(metadata) if metadata else {}
        except json.JSONDecodeError:
            custom_metadata = {"raw_metadata": metadata}

        # Validate memory type
        if memory_type not in MEMORY_TYPES:
            return f"Error: Invalid memory_type '{memory_type}'. Must be one of: {', '.join(MEMORY_TYPES)}"

        # Store the memory
        manager = get_memory_manager()
        memory_id = manager.store(
            content=content,
            memory_type=memory_type,
            metadata=custom_metadata,
            source="tool",
        )

        return f"Memory stored successfully. ID: {memory_id}"

    except MemoryManagerError as e:
        logger.error(f"Failed to store memory: {e}")
        return f"Error storing memory: {e}"
    except Exception as e:
        logger.error(f"Unexpected error storing memory: {e}")
        return f"Error: {e}"


@theo_tool
def search_memory(
    query: str,
    memory_type: str = "",
    k: int = 5,
) -> str:
    """
    Search semantic memory for previously stored information using natural language.

    USE THIS TOOL WHEN:
    - User asks "what do you know about me/X?" or "do you remember...?"
    - You need to recall stored preferences, facts, or context
    - Looking up previously saved research, documents, or tool outputs
    - User references something from a past conversation
    - Examples: "What are my dietary restrictions?", "What tech stack am I using?"

    DO NOT USE THIS TOOL WHEN:
    - The information is already in the current conversation context
    - Asking about general knowledge (not user-specific stored info)
    - You just stored something and already have the result
    - The query is too vague to be useful

    Args:
        query: Natural language search query describing what you're looking for.
               Be specific: "user food allergies" is better than "allergies"
        memory_type: Optional filter - "general", "document", "conversation", "tool_output"
                    Leave empty to search all types.
        k: Number of results (1-20, default 5). Use fewer for focused queries.

    Returns:
        JSON array of matching memories with content, type, relevance score, and timestamp.

    Examples:
        search_memory("user dietary preferences and allergies", "general", 3)
        search_memory("project technology stack", "document", 5)
    """
    try:
        # Validate k
        k = min(max(1, k), 20)

        # Validate memory type if provided
        if memory_type and memory_type not in MEMORY_TYPES:
            return f"Error: Invalid memory_type '{memory_type}'. Must be one of: {', '.join(MEMORY_TYPES)}"

        # Search memories
        manager = get_memory_manager()
        results = manager.search(
            query=query,
            memory_type=memory_type if memory_type else None,
            k=k,
        )

        if not results:
            return "No matching memories found."

        # Format results
        formatted_results = []
        for i, memory in enumerate(results, 1):
            formatted_results.append({
                "rank": i,
                "memory_id": memory["memory_id"],
                "content": memory["content"],
                "type": memory["memory_type"],
                "score": round(memory["score"], 3),
                "timestamp": memory["timestamp"],
            })

        return json.dumps(formatted_results, indent=2)

    except Exception as e:
        logger.error(f"Error searching memory: {e}")
        return f"Error searching memory: {e}"


@theo_tool
def forget_memory(identifier: str) -> str:
    """
    Delete a memory by ID or by searching for matching content.

    USE THIS TOOL WHEN:
    - User explicitly says "forget that", "delete that memory", or "that's no longer true"
    - Stored information has become outdated or incorrect
    - User wants to remove sensitive or private information
    - Cleaning up duplicate or redundant memories
    - Examples: "Forget my old address", "I'm no longer vegetarian, update that"

    DO NOT USE THIS TOOL WHEN:
    - User just wants to update information (store new memory instead, old will be less relevant)
    - You're unsure which memory to delete (use list_memories or search_memory first)
    - The memory might still be useful in the future
    - User hasn't explicitly asked to forget something

    Args:
        identifier: Either a memory ID (UUID like "550e8400-e29b-41d4-a716-446655440000")
                   OR a search query to find and delete the best matching memory.
                   Using ID is more precise; using query deletes the top match.

    Returns:
        Confirmation of deletion, or message if no matching memory found.

    Examples:
        forget_memory("550e8400-e29b-41d4-a716-446655440000")  # Precise deletion by ID
        forget_memory("old home address")  # Finds and deletes best match
    """
    try:
        if not identifier or not identifier.strip():
            return "Error: Please provide a memory ID or search query."

        manager = get_memory_manager()
        success = manager.delete(identifier.strip())

        if success:
            return f"Memory deleted successfully."
        else:
            return "No matching memory found to delete."

    except Exception as e:
        logger.error(f"Error deleting memory: {e}")
        return f"Error deleting memory: {e}"


@theo_tool
def list_memories(
    memory_type: str = "",
    limit: int = 10,
) -> str:
    """
    List recent memories, optionally filtered by type.

    USE THIS TOOL WHEN:
    - User asks "what do you have stored?" or "show me my memories"
    - You need to browse available memories without a specific search query
    - User wants to see an overview of stored information
    - Debugging or auditing what's in the memory system
    - User asks to "list", "show all", or "display" memories

    DO NOT USE THIS TOOL WHEN:
    - You're looking for specific information (use search_memory instead)
    - User asks a question that needs semantic matching (use search_memory)
    - You just want to check if a specific fact exists (use search_memory)
    - The user hasn't asked about memory contents

    Args:
        memory_type: Optional filter by type - "general", "document", "conversation", "tool_output"
                    Leave empty to list all types.
        limit: Number of memories to return (1-50, default 10). Use smaller limits for overview.

    Returns:
        JSON with count and array of memories (content truncated to 200 chars).

    Examples:
        list_memories("", 5)  # List 5 most recent memories of any type
        list_memories("document", 10)  # List up to 10 document memories
    """
    try:
        # Validate limit
        limit = min(max(1, limit), 50)

        # Validate memory type if provided
        if memory_type and memory_type not in MEMORY_TYPES:
            return f"Error: Invalid memory_type '{memory_type}'. Must be one of: {', '.join(MEMORY_TYPES)}"

        # List memories
        manager = get_memory_manager()
        memories = manager.list_memories(
            memory_type=memory_type if memory_type else None,
            limit=limit,
        )

        if not memories:
            type_msg = f" of type '{memory_type}'" if memory_type else ""
            return f"No memories found{type_msg}."

        # Format results
        formatted = []
        for memory in memories:
            formatted.append({
                "memory_id": memory["memory_id"],
                "content": memory["content"][:200] + "..." if len(memory["content"]) > 200 else memory["content"],
                "type": memory["memory_type"],
                "timestamp": memory["timestamp"],
                "source": memory["source"],
            })

        # Add summary
        result = {
            "count": len(formatted),
            "memories": formatted,
        }

        return json.dumps(result, indent=2)

    except Exception as e:
        logger.error(f"Error listing memories: {e}")
        return f"Error listing memories: {e}"


@theo_tool
def memory_stats() -> str:
    """
    Get statistics about the memory system.

    USE THIS TOOL WHEN:
    - User asks "how many memories do you have?" or "memory status"
    - Diagnosing memory system issues or checking if it's working
    - User wants to know storage usage or configuration
    - Checking if memories exist before deciding to store more

    DO NOT USE THIS TOOL WHEN:
    - User wants to see actual memory contents (use list_memories or search_memory)
    - Looking for specific information (use search_memory)
    - Storing or deleting memories (use store_memory or forget_memory)
    - The user hasn't asked about memory system status

    Returns:
        JSON with total_memories count, collection_name, vector_dimensions, and storage path.

    Example:
        memory_stats()  # Returns {"total_memories": 42, "collection_name": "theo_memories", ...}
    """
    try:
        manager = get_memory_manager()
        stats = manager.get_stats()

        if not stats:
            return "Unable to retrieve memory statistics."

        return json.dumps(stats, indent=2)

    except Exception as e:
        logger.error(f"Error getting memory stats: {e}")
        return f"Error getting memory stats: {e}"
