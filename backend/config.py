"""Shared configuration: OpenAI client, HTTP client, constants."""

import json
from pathlib import Path

import httpx
from openai import OpenAI

# Path to corporate CA cert
CA_CERT = "corporate-ca.pem"

# Shared HTTP client (used by tools that make external API calls)
http_client = httpx.Client(verify=CA_CERT)

# OpenAI client
openai_client = OpenAI(http_client=http_client)

# Agent settings
MAX_AGENT_ITERATIONS = 10
MODEL = "gpt-4o"

# MCP server configuration
MCP_CONFIG_FILE = Path("mcp_servers.json")


def load_mcp_config() -> dict:
    """Load MCP server configuration from JSON file."""
    if not MCP_CONFIG_FILE.exists():
        return {}
    with open(MCP_CONFIG_FILE, "r") as f:
        data = json.load(f)
    return data.get("servers", {})
