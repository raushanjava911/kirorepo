"""Agent registry — collects all specialized sub-agents."""

from agents.weather_agent import run as run_weather_agent
from agents.research_agent import run as run_research_agent
from agents.math_agent import run as run_math_agent

# Map of agent name → run function
AGENTS = {
    "weather_agent": run_weather_agent,
    "research_agent": run_research_agent,
    "math_agent": run_math_agent,
}
