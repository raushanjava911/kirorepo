FROM python:3.12-slim

WORKDIR /app

# Install corporate CA certificate
COPY corporate-ca.pem /usr/local/share/ca-certificates/corporate-ca.crt
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY corporate-ca.pem .
COPY config.py .
COPY orchestrator.py .
COPY mcp_client.py .
COPY mcp_server.py .
COPY mcp_servers.json .
COPY agent.py .
COPY app.py .
COPY tools/ tools/
COPY agents/ agents/

# Copy HR policy documents
COPY documents/ documents/

EXPOSE 5000

CMD ["python", "app.py"]
