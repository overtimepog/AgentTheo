"""
Calculator Tool

Provides mathematical expression evaluation.
"""

from src.registry import agent_tool


@agent_tool
def calculator(expression: str) -> str:
    """
    Evaluate a mathematical expression and return the numeric result.

    USE THIS TOOL WHEN:
    - User explicitly asks to calculate, compute, or solve a math problem
    - You need arithmetic operations: add, subtract, multiply, divide, modulo
    - You need mathematical functions: sqrt, sin, cos, tan, log, exp, pow
    - You need to compute percentages, ratios, or complex expressions
    - Examples: "what's 25% of 340?", "calculate 2^10", "sqrt(144)", "15 * 23"

    DO NOT USE THIS TOOL WHEN:
    - The question contains numbers but isn't asking for a calculation
    - The math is trivial (2+2, 10/2) - just answer directly
    - You need current date/time - use get_current_time instead
    - You're counting items or doing non-numeric operations

    Args:
        expression: Mathematical expression using Python syntax.
                   Supports: +, -, *, /, **, % (modulo)
                   Functions: sqrt(), sin(), cos(), tan(), log(), log10(), exp(), pow(), abs(), round(), min(), max()
                   Constants: pi, e, tau

    Returns:
        The numeric result as a string, or an error message if invalid.

    Examples:
        calculator("230 * 0.15") -> "34.5" (15% of 230)
        calculator("sqrt(144)") -> "12.0"
        calculator("2 ** 10") -> "1024"
        calculator("sin(pi/2)") -> "1.0"
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
