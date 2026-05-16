"""Orchestrator Agent — routes user queries to specialized sub-agents."""

import json

from config import openai_client, MODEL, MAX_AGENT_ITERATIONS
from agents import AGENTS

ORCHESTRATOR_SYSTEM_PROMPT = """You are an orchestrator agent that manages a team of specialized sub-agents.

Your job is to:
1. Understand the user's question
2. Decide which sub-agent(s) should handle it
3. Delegate the work by calling the appropriate agent(s)
4. Combine their responses into a single, coherent final answer

Your available sub-agents:

- weather_agent: Handles weather, temperature, forecasts, climate conditions, current date/time, and timezone questions.
- research_agent: Handles factual questions about people, places, events, history, science, technology. Uses Wikipedia.
- math_agent: Handles calculations, math problems, unit conversions, numerical comparisons.

Rules:
1. For simple questions, delegate to ONE agent.
2. For complex questions that span multiple domains, call MULTIPLE agents and combine their answers.
3. Always delegate — do NOT try to answer questions yourself without using an agent.
4. After receiving agent responses, synthesize them into a clear, unified answer for the user.
5. If a question doesn't fit any agent well, use the research_agent as a fallback.

Examples:
- "What's the weather in Paris?" → weather_agent
- "Tell me about Einstein" → research_agent
- "What's 2^10?" → math_agent
- "What's the weather in Tokyo and tell me about the city" → weather_agent + research_agent
- "Is the temperature in London higher than sqrt(900)?" → weather_agent + math_agent
"""

# The orchestrator's "tools" are the sub-agents
ORCHESTRATOR_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "weather_agent",
            "description": "Delegate to the weather specialist. Handles weather, temperature, forecasts, current date/time, timezone queries.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "The specific task or question to delegate to the weather agent.",
                    }
                },
                "required": ["task"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "research_agent",
            "description": "Delegate to the research specialist. Handles factual questions about people, places, events, history, science, technology using Wikipedia.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "The specific task or question to delegate to the research agent.",
                    }
                },
                "required": ["task"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "math_agent",
            "description": "Delegate to the math specialist. Handles calculations, math problems, unit conversions, numerical comparisons.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "The specific task or question to delegate to the math agent.",
                    }
                },
                "required": ["task"],
            },
        },
    },
]


def run_orchestrator(messages: list) -> dict:
    """
    Orchestrator loop:
    1. Receives user messages
    2. Decides which sub-agent(s) to call
    3. Executes sub-agents and collects results
    4. Synthesizes a final answer

    Returns dict with 'reply', 'tools_used' (which agents were called and their results).
    """
    # Prepend orchestrator system prompt
    if not messages or messages[0].get("role") != "system":
        messages = [{"role": "system", "content": ORCHESTRATOR_SYSTEM_PROMPT}] + messages

    agents_called_log = []

    for iteration in range(MAX_AGENT_ITERATIONS):
        response = openai_client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=ORCHESTRATOR_TOOLS,
        )

        choice = response.choices[0]

        # If the orchestrator is done, return the final synthesized answer
        if choice.finish_reason != "tool_calls":
            return {
                "reply": choice.message.content,
                "tools_used": agents_called_log,
            }

        # Orchestrator wants to delegate to sub-agent(s)
        assistant_message = choice.message
        messages.append(assistant_message)

        for tool_call in assistant_message.tool_calls:
            agent_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            task = args.get("task", "")

            # Execute the sub-agent
            if agent_name in AGENTS:
                result = AGENTS[agent_name](task)
            else:
                result = f"Error: Unknown agent '{agent_name}'"

            # Log for transparency
            agents_called_log.append({
                "tool": agent_name,
                "args": {"task": task},
                "result": result,
            })

            # Feed sub-agent result back to orchestrator
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })

    return {
        "reply": "Orchestrator reached maximum iterations.",
        "tools_used": agents_called_log,
    }
