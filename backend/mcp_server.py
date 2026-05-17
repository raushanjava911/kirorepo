"""MCP Server — exposes your agent's tools so other AI apps can use them."""

from mcp.server.fastmcp import FastMCP

from tools.date_tool import get_current_date
from tools.weather_tool import get_current_weather
from tools.calc_tool import calculate
from tools.wiki_tool import search_wikipedia
from tools.email_tool import send_email
from tools.hr_policy_tool import search_hr_policy

# Create the MCP server
mcp = FastMCP(
    name="ai-agent-tools",
    description="AI Agent tools: weather, date/time, calculator, Wikipedia, email, HR policy search",
)


# --- Expose tools as MCP resources ---

@mcp.tool()
def get_date(timezone: str = "UTC") -> str:
    """Get the current date and time in a given timezone (e.g. 'UTC', 'Asia/Kolkata', 'US/Eastern')."""
    return get_current_date(timezone)


@mcp.tool()
def get_weather(location: str) -> str:
    """Get current weather for a location including temperature, conditions, and wind speed."""
    return get_current_weather(location)


@mcp.tool()
def calc(expression: str) -> str:
    """Evaluate a math expression (e.g. '2**10', 'math.sqrt(144)', '(5+3)*2')."""
    return calculate(expression)


@mcp.tool()
def wiki_search(query: str) -> str:
    """Search Wikipedia for factual information about a topic."""
    return search_wikipedia(query)


@mcp.tool()
def email(to: str, subject: str, body: str) -> str:
    """Send an email to a recipient with a subject and body."""
    return send_email(to, subject, body)


@mcp.tool()
def hr_policy(query: str) -> str:
    """Search company HR policy documents for information about leave, benefits, conduct, etc."""
    return search_hr_policy(query)


if __name__ == "__main__":
    mcp.run()
