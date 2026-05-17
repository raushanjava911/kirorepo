"""Flask app — thin HTTP layer that wires routes to the orchestrator."""

from flask import Flask, request, jsonify
from flask_cors import CORS

from config import load_mcp_config
from mcp_client import init_mcp_client
from orchestrator import run_orchestrator

app = Flask(__name__)
CORS(app)

# Initialize MCP client with configured servers
mcp_servers = load_mcp_config()
if mcp_servers:
    print(f"[MCP] Connecting to {len(mcp_servers)} server(s)...")
    init_mcp_client(mcp_servers)
else:
    print("[MCP] No external MCP servers configured.")


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()
    messages = data.get("messages", [])

    if not messages:
        return jsonify({"error": "No messages provided"}), 400

    try:
        result = run_orchestrator(messages)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
