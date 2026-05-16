FROM python:3.12-slim

WORKDIR /app

# Install the corporate CA certificate so pip (and the app) can verify SSL
COPY corporate-ca.pem /usr/local/share/ca-certificates/corporate-ca.crt
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the CA certificate and application code
COPY corporate-ca.pem .
COPY chat_openai.py .

CMD ["python", "-u", "chat_openai.py"]
