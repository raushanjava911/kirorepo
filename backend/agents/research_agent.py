"""Research Agent — specialized in factual lookups and knowledge questions."""

import json

from config import openai_client, MODEL
from tools.wiki_tool import TOOL_DEFINITION as wiki_def, search_wikipedia

SYSTEM_PROMPT = """You are a research specialist agent.

Your job:
- Answer factual questions about people, places, events, science, history, technology
- Look up information on Wikipedia when you need accurate facts
- Summarize and explain complex topics clearly

Always use your Wikipedia tool for factual claims — don't rely on memory alone.
Present information in a clear, well-organized way. Cite that the information
comes from Wikipedia when relevant.
"""

TOOLS = [wiki_def]

TOOL_FUNCTIONS = {
    "search_wikipedia": search_wikipedia,
}

MAX_ITERATIONS = 5


def run(task: str) -> str:
    """Execute the research agent with the given task."""
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

    return "Research agent reached maximum iterations without a final answer."
