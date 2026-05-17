"""Orchestrator Agent — routes user queries to specialized sub-agents and MCP tools."""

import json

from config import openai_client, MODEL, MAX_AGENT_ITERATIONS
from agents import AGENTS
from mcp_client import get_mcp_tool_schemas, call_mcp_tool, is_mcp_tool

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
- hr_agent: Handles questions about company HR policies — leave, attendance, benefits, appraisals, code of conduct, holidays, work from home, dress code, etc.
- email_agent: Handles composing and sending emails. Use when the user wants to send, write, or email someone.

You may also have additional tools from external MCP servers (prefixed with their server name).
Use these when the task matches their description.

Rules:
1. For simple questions, delegate to ONE agent.
2. For complex questions that span multiple domains, call MULTIPLE agents and combine their answers.
3. Always delegate — do NOT try to answer questions yourself without using an agent.
4. After receiving agent responses, synthesize them into a clear, unified answer for the user.
5. If a question doesn't fit any agent well, use the research_agent as a fallback.
6. For MCP tools, call them directly — they are not agents, just tools.

Examples:
- "What's the weather in Paris?" → weather_agent
- "Tell me about Einstein" → research_agent
- "What's 2^10?" → math_agent
- "What's the leave policy?" → hr_agent
- "How many casual leaves do I get?" → hr_agent
- "Send an email to john@example.com about the meeting" → email_agent
- "Email my manager that I'll be late" → email_agent
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
    {
        "type": "function",
        "function": {
            "name": "hr_agent",
            "description": "Delegate to the HR policy specialist. Handles questions about company policies — leave, attendance, benefits, appraisals, code of conduct, holidays, work from home, dress code, and any HR-related queries.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "The specific HR policy question to delegate to the HR agent.",
                    }
                },
                "required": ["task"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "email_agent",
            "description": "Delegate to the email specialist. Handles composing and sending emails to recipients.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "The email task including recipient, subject/topic, and any content details.",
                    }
                },
                "required": ["task"],
            },
        },
    },
]


def _get_all_tools() -> list[dict]:
    """Combine agent tools + MCP tools."""
    mcp_tools = get_mcp_tool_schemas()
    return ORCHESTRATOR_TOOLS + mcp_tools


def run_orchestrator(messages: list) -> dict:
    """
    Orchestrator loop:
    1. Receives user messages
    2. Decides which sub-agent(s) or MCP tool(s) to call
    3. Executes them and collects results
    4. Synthesizes a final answer

    Returns dict with 'reply', 'tools_used' (which agents/tools were called and their results).
    """
    # Prepend orchestrator system prompt
    if not messages or messages[0].get("role") != "system":
        messages = [{"role": "system", "content": ORCHESTRATOR_SYSTEM_PROMPT}] + messages

    all_tools = _get_all_tools()
    agents_called_log = []

    for iteration in range(MAX_AGENT_ITERATIONS):
        response = openai_client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=all_tools,
        )

        choice = response.choices[0]

        # If the orchestrator is done, return the final synthesized answer
        if choice.finish_reason != "tool_calls":
            return {
                "reply": choice.message.content,
                "tools_used": agents_called_log,
            }

        # Orchestrator wants to delegate to sub-agent(s) or call MCP tool(s)
        assistant_message = choice.message
        messages.append(assistant_message)

        for tool_call in assistant_message.tool_calls:
            tool_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)

            # Determine if it's a sub-agent or an MCP tool
            if tool_name in AGENTS:
                task = args.get("task", "")
                result = AGENTS[tool_name](task)
                log_args = {"task": task}
            elif is_mcp_tool(tool_name):
                result = call_mcp_tool(tool_name, args)
                log_args = args
            else:
                result = f"Error: Unknown agent/tool '{tool_name}'"
                log_args = args

            # Log for transparency
            agents_called_log.append({
                "tool": tool_name,
                "args": log_args,
                "result": result,
            })

            # Feed result back to orchestrator
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })

    return {
        "reply": "Orchestrator reached maximum iterations.",
        "tools_used": agents_called_log,
    }
