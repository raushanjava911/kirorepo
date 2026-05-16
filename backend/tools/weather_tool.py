"""Tool: Get current weather for a location."""

from config import http_client

TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "get_current_weather",
        "description": "Get current weather for a location including temperature, conditions, and wind speed. Use when the user asks about weather, temperature, or climate conditions.",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City or place name, e.g. 'London', 'New York', 'Mumbai', 'Tokyo'.",
                }
            },
            "required": ["location"],
        },
    },
}

WEATHER_DESCRIPTIONS = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy",
    3: "Overcast", 45: "Foggy", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snowfall", 73: "Moderate snowfall", 75: "Heavy snowfall",
    80: "Slight rain showers", 81: "Moderate rain showers",
    82: "Violent rain showers", 95: "Thunderstorm",
    96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail",
}


def get_current_weather(location: str) -> str:
    """Fetch current weather from Open-Meteo (free, no API key)."""
    try:
        # Geocode location
        geo_resp = http_client.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": location, "count": 1},
        )
        geo_data = geo_resp.json()

        if not geo_data.get("results"):
            return f"Could not find location: {location}"

        place = geo_data["results"][0]
        lat = place["latitude"]
        lon = place["longitude"]
        name = place.get("name", location)
        country = place.get("country", "")

        # Get weather
        weather_resp = http_client.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current_weather": True,
            },
        )
        weather_data = weather_resp.json()
        current = weather_data["current_weather"]

        temp = current["temperature"]
        windspeed = current["windspeed"]
        weather_code = current["weathercode"]
        condition = WEATHER_DESCRIPTIONS.get(weather_code, f"Code {weather_code}")

        return (
            f"Weather in {name}, {country}:\n"
            f"  Temperature: {temp}°C\n"
            f"  Condition: {condition}\n"
            f"  Wind Speed: {windspeed} km/h"
        )
    except Exception as e:
        return f"Error fetching weather: {str(e)}"
