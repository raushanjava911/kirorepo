"""Shared configuration: OpenAI client, HTTP client, constants."""

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
