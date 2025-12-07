"""
String Tools

Provides string manipulation utilities.
"""

from src.registry import theo_tool


@theo_tool
def reverse_string(text: str) -> str:
    """
    Reverse the characters in a string.

    USE THIS TOOL WHEN:
    - User explicitly asks to reverse a string or text
    - User wants to see text backwards
    - Checking for palindromes (reverse and compare)
    - Examples: "reverse 'hello'", "what's 'racecar' backwards?"

    DO NOT USE THIS TOOL WHEN:
    - User asks to reverse a list or array (not a string)
    - User wants to reverse word order (this reverses characters)
    - User is asking about string manipulation conceptually
    - You can easily reverse a short string mentally (e.g., "abc" -> "cba")

    Args:
        text: The string to reverse. Can be any length.

    Returns:
        The input string with characters in reverse order.

    Examples:
        reverse_string("hello") -> "olleh"
        reverse_string("Python") -> "nohtyP"
        reverse_string("12345") -> "54321"
    """
    return text[::-1]
