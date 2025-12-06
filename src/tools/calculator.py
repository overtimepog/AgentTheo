"""
Calculator Tool

Provides mathematical expression evaluation.
"""

from src.registry import agent_tool


@agent_tool
def calculator(expression: str) -> str:
    """
    Evaluate a mathematical expression.
    
    Args:
        expression: A mathematical expression like "2 + 2" or "sqrt(16)"
    
    Returns:
        The result of the calculation as a string.
    """
    import math
    # Safe eval with math functions
    allowed = {
        k: v for k, v in math.__dict__.items() 
        if not k.startswith("_")
    }
    allowed.update({"abs": abs, "round": round, "min": min, "max": max})
    try:
        result = eval(expression, {"__builtins__": {}}, allowed)
        return str(result)
    except Exception as e:
        return f"Error: {e}"
