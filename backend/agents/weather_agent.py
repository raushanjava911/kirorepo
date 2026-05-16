"""Weather Agent — specialized in weather, forecasts, and date/time queries."""

import json

from config import openai_client, MODEL
from tools.date_tool import TOOL_DEFINITION as date_def, get_current_date
from tools.weather_tool import TOOL_DEFINITION as weather_def, get_current_weather

SYSTEM_PROMPT = """You are a weather and time specialist agent.

Your job:
- Answer questions about current weather, temperature, conditions, and forecasts
- Provide current date and time in any timezone
- Give practical advice based on weather (what to wear, carry umbrella, etc.)

You have access to real-time weather data and time information. Always use your tools
to get accurate data — never guess weather or time.

Be concise and informative. Include relevant details like temperature, conditions,
and wind speed when reporting weather.
"""

TOOLS = [date_def, weather_def]

TOOL_FUNCTIONS = {
    "get_current_date": get_current_date,
    "get_current_weather": get_current_weather,
}

MAX_ITERATIONS = 5


def run(task: str) -> str:
    """Execute the weather agent with the given task."""
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

    return "Weather agent reached maximum iterations without a final answer."
