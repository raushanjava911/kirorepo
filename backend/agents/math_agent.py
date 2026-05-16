"""Math Agent — specialized in calculations and mathematical reasoning."""

import json

from config import openai_client, MODEL
from tools.calc_tool import TOOL_DEFINITION as calc_def, calculate

SYSTEM_PROMPT = """You are a mathematics specialist agent.

Your job:
- Perform calculations (arithmetic, algebra, trigonometry, etc.)
- Solve math problems step by step
- Explain mathematical concepts clearly
- Handle unit conversions and numerical comparisons

Always use your calculator tool for actual computations — don't do mental math.
Show your work and explain the steps when solving problems.
"""

TOOLS = [calc_def]

TOOL_FUNCTIONS = {
    "calculate": calculate,
}

MAX_ITERATIONS = 5


def run(task: str) -> str:
    """Execute the math agent with the given task."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": task},
    ]

    for _ in range(MAX_ITERATIONS):
        response = openai_client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
        )

        choice = response.choices[0]

        if choice.finish_reason != "tool_calls":
            return choice.message.content

        # Execute tool calls
        assistant_message = choice.message
        messages.append(assistant_message)

        for tool_call in assistant_message.tool_calls:
            fn_name = tool_call.function.name
            fn_args = json.loads(tool_call.function.arguments)

            if fn_name in TOOL_FUNCTIONS:
                result = TOOL_FUNCTIONS[fn_name](**fn_args)
            else:
                result = f"Error: Unknown tool '{fn_name}'"

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })

    return "Math agent reached maximum iterations without a final answer."
