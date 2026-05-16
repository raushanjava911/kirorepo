"""Simple chat program that talks to the OpenAI API."""

import httpx
from openai import OpenAI

# Path to your corporate/custom CA certificate
CA_CERT = "corporate-ca.pem"


def main():
    # Point the HTTP client at your .cer file for SSL verification
    http_client = httpx.Client(verify=CA_CERT)
    client = OpenAI(http_client=http_client)

    print("Chat with OpenAI (type 'quit' to exit)\n")

    messages = []

    while True:
        user_input = input("You: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit"):
            print("Goodbye!")
            break

        messages.append({"role": "user", "content": user_input})

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
        )

        assistant_message = response.choices[0].message.content
        messages.append({"role": "assistant", "content": assistant_message})

        print(f"\nAssistant: {assistant_message}\n")


if __name__ == "__main__":
    main()
