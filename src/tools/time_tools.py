"""
Time Tools

Provides time and date related utilities.
"""

from src.registry import agent_tool


@agent_tool
def get_current_time() -> str:
    """
    Get the current date and time in the local timezone.

    USE THIS TOOL WHEN:
    - User asks "what time is it?" or "what's today's date?"
    - User needs the current date for context (e.g., "is it still 2024?")
    - You need to timestamp something or reference "now"
    - User asks about day of week, month, or year

    DO NOT USE THIS TOOL WHEN:
    - User asks about a specific date in the past or future
    - User asks to calculate time differences (use calculator for math)
    - User asks about timezones other than local (not supported)
    - The current time/date is not relevant to the question

    Returns:
        Current datetime as "YYYY-MM-DD HH:MM:SS" format string.

    Examples:
        "What time is it?" -> get_current_time() -> "2025-12-06 14:30:45"
        "What's today's date?" -> get_current_time() -> "2025-12-06 14:30:45"
    """
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
