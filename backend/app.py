"""Flask backend that proxies chat requests to OpenAI."""

import httpx
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

app = Flask(__name__)
CORS(app)

# Path to corporate CA cert (adjust if needed)
CA_CERT = "corporate-ca.pem"

http_client = httpx.Client(verify=CA_CERT)
client = OpenAI(http_client=http_client)


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()
    messages = data.get("messages", [])

    if not messages:
        return jsonify({"error": "No messages provided"}), 400

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
        )
        assistant_message = response.choices[0].message.content
        return jsonify({"reply": assistant_message})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
