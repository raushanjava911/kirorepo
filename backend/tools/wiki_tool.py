"""Tool: Wikipedia search."""

from config import http_client

TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "search_wikipedia",
        "description": "Search Wikipedia for factual information about a topic. Use when the user asks about people, places, events, science, history, or any factual topic.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The topic to search for on Wikipedia.",
                }
            },
            "required": ["query"],
        },
    },
}


def search_wikipedia(query: str) -> str:
    """Search Wikipedia and return a summary."""
    try:
        # Try direct page summary first
        resp = http_client.get(
            "https://en.wikipedia.org/api/rest_v1/page/summary/" + query.replace(" ", "_"),
        )

        if resp.status_code == 404:
            # Fall back to search
            search_resp = http_client.get(
                "https://en.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "list": "search",
                    "srsearch": query,
                    "format": "json",
                    "srlimit": 1,
                },
            )
            search_data = search_resp.json()
            results = search_data.get("query", {}).get("search", [])
            if not results:
                return f"No Wikipedia article found for: {query}"

            title = results[0]["title"]
            resp = http_client.get(
                "https://en.wikipedia.org/api/rest_v1/page/summary/" + title.replace(" ", "_"),
            )

        data = resp.json()
        title = data.get("title", query)
        extract = data.get("extract", "No summary available.")

        if len(extract) > 1000:
            extract = extract[:1000] + "..."

        return f"Wikipedia: {title}\n\n{extract}"
    except Exception as e:
        return f"Error searching Wikipedia: {str(e)}"
