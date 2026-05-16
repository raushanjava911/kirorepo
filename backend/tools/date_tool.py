"""Tool: Get current date and time."""

from datetime import datetime
from zoneinfo import ZoneInfo

TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "get_current_date",
        "description": "Get the current date and time. Use when the user asks for today's date, current time, day of the week, or anything requiring real-time date/time.",
        "parameters": {
            "type": "object",
            "properties": {
                "timezone": {
                    "type": "string",
                    "description": "Timezone like 'UTC', 'Asia/Kolkata', 'US/Eastern', 'Europe/London'. Defaults to UTC.",
                }
            },
            "required": [],
        },
    },
}


def get_current_date(timezone: str = "UTC") -> str:
    """Return the current date and time as a formatted string."""
    try:
        tz = ZoneInfo(timezone)
    except Exception:
        tz = ZoneInfo("UTC")

    now = datetime.now(tz)
    return now.strftime("%A, %B %d, %Y %I:%M:%S %p %Z")
