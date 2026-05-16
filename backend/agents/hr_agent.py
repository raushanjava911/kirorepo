"""HR Policy Agent — specialized in answering company HR policy questions."""

import json

from config import openai_client, MODEL
from tools.hr_policy_tool import TOOL_DEFINITION as hr_def, search_hr_policy

SYSTEM_PROMPT = """You are an HR policy specialist agent for the company.

Your job:
- Answer questions about company HR policies accurately based on the policy documents
- Cover topics like leave, attendance, benefits, appraisals, code of conduct, holidays, WFH, etc.
- Always search the policy documents before answering — never make up policies
- Quote relevant sections when possible
- If the policy documents don't cover a topic, clearly say so and suggest the user contact HR directly

Be helpful, clear, and precise. Employees rely on your answers for important decisions.
"""

TOOLS = [hr_def]

TOOL_FUNCTIONS = {
    "search_hr_policy": search_hr_policy,
}

MAX_ITERATIONS = 5


def run(task: str) -> str:
    """Execute the HR policy agent with the given task."""
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

    return "HR agent reached maximum iterations without a final answer."
