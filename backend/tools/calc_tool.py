"""Tool: Mathematical calculator."""

import math

TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "calculate",
        "description": "Perform a mathematical calculation. Supports basic arithmetic, powers, square roots, trigonometry, etc. Use when the user needs math computed.",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "A Python math expression to evaluate, e.g. '2**10', 'math.sqrt(144)', '(5+3)*2'.",
                }
            },
            "required": ["expression"],
        },
    },
}


def calculate(expression: str) -> str:
    """Safely evaluate a math expression."""
    allowed_names = {
        "math": math,
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "sum": sum,
        "pow": pow,
    }
    try:
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        return f"{expression} = {result}"
    except Exception as e:
        return f"Error calculating '{expression}': {str(e)}"
