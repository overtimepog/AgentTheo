"""
String Tools

Provides string manipulation utilities.
"""

from src.registry import agent_tool


@agent_tool  
def reverse_string(text: str) -> str:
    """
    Reverse a string.
    
    Args:
        text: The string to reverse.
    
    Returns:
        The reversed string.
    """
    return text[::-1]
