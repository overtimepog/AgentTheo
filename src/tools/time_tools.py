"""
Time Tools

Provides time and date related utilities.
"""

from src.registry import agent_tool


@agent_tool
def get_current_time() -> str:
    """
    Get the current date and time.
    
    Returns:
        Current datetime as a formatted string.
    """
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
