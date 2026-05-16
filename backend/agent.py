"""Agent loop — orchestrates reasoning and tool calling."""

import json

from config import openai_client, MAX_AGENT_ITERATIONS, MODEL
from tools import TOOLS, TOOL_FUNCTIONS

AGENT_SYSTEM_PROMPT = """You are an intelligent assistant with access to real-time tools.

Your capabilities:
- Get the current date and time in any timezone
- Get current weather for any location
- Perform mathematical calculations
- Search Wikipedia for factual information

Instructions:
1. When a question requires real-time or factual data, USE your tools. Do not guess.
2. Think step by step. If a question needs multiple pieces of information, call tools one at a time and combine the results.
3. After gathering all needed information, provide a complete, well-structured answer.
4. If a tool returns an error, acknowledge it and try an alternative approach.
5. Be concise but thorough.

Examples of multi-step reasoning:
- "Should I carry an umbrella tomorrow in London?" → get date → get weather → advise
- "What's the time difference between Tokyo and New York?" → get time in both → calculate difference
- "Tell me about the Eiffel Tower and today's weather in Paris" → search Wikipedia → get weather → combine
"""


def run_agent(messages: list) -> dict:
    """
    The core agent loop:
    1. Send messages + tools to OpenAI
    2. If the model calls tools, execute them and feed results back
    3. Repeat until the model gives a final text response (or max iterations hit)

    Returns dict with 'reply' and 'tools_used' for transparency.
    """
    # Prepend system prompt if not already present
    if not messages or messages[0].get("role") != "system":
        messages = [{"role": "system", "content": AGENT_SYSTEM_PROMPT}] + messages

    tool_calls_log = []

    for iteration in range(MAX_AGENT_ITERATIONS):
        response = openai_client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
        )

        choice = response.choices[0]

        # If the model gives a text reply, we're done
        if choice.finish_reason != "tool_calls":
            return {
                "reply": choice.message.content,
                "tools_used": tool_calls_log,
            }

        # Model wants to call tools — execute them
        assistant_message = choice.message
        messages.append(assistant_message)

        for tool_call in assistant_message.tool_calls:
            fn_name = tool_call.function.name
            fn_args = json.loads(tool_call.function.arguments)

            # Execute the tool
            if fn_name in TOOL_FUNCTIONS:
                result = TOOL_FUNCTIONS[fn_name](**fn_args)
            else:
                result = f"Error: Unknown tool '{fn_name}'"

            # Log for transparency
            tool_calls_log.append({
                "tool": fn_name,
                "args": fn_args,
                "result": result,
            })

            # Feed result back to the model
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })

    # Max iterations reached
    return {
        "reply": "I've reached my maximum reasoning steps. Here's what I found so far based on the tools I called.",
        "tools_used": tool_calls_log,
    }
