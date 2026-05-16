"""Tool registry — collects all tool definitions and implementations."""

from tools.date_tool import TOOL_DEFINITION as date_def, get_current_date
from tools.weather_tool import TOOL_DEFINITION as weather_def, get_current_weather
from tools.calc_tool import TOOL_DEFINITION as calc_def, calculate
from tools.wiki_tool import TOOL_DEFINITION as wiki_def, search_wikipedia

# List of tool schemas sent to OpenAI
TOOLS = [date_def, weather_def, calc_def, wiki_def]

# Map of tool name → implementation function
TOOL_FUNCTIONS = {
    "get_current_date": get_current_date,
    "get_current_weather": get_current_weather,
    "calculate": calculate,
    "search_wikipedia": search_wikipedia,
}
