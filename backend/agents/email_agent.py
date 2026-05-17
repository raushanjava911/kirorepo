"""Email Agent — specialized in composing and sending emails."""

import json

from config import openai_client, MODEL
from tools.email_tool import TOOL_DEFINITION as email_def, send_email

SYSTEM_PROMPT = """You are an email specialist agent.

Your job:
- Help users compose and send emails
- Ask for clarification if the recipient, subject, or body is unclear
- Write professional, clear email content when the user gives a rough idea
- Confirm the details before sending

Rules:
1. Always use the send_email tool to actually send the email.
2. If the user says "email John about the meeting tomorrow", compose a professional email and send it.
3. If the user provides a rough message, polish it into a proper email while keeping their intent.
4. Include a greeting and sign-off in the email body.
5. If the recipient email address is missing, state that you need it — don't guess.
"""

TOOLS = [email_def]

TOOL_FUNCTIONS = {
    "send_email": send_email,
}

MAX_ITERATIONS = 5


def run(task: str) -> str:
    """Execute the email agent with the given task."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": task},
    ]

    for _ in range(MAX_ITERATIONS):
        response = openai_client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
        )

        choice = response.choices[0]

        if choice.finish_reason != "tool_calls":
            return choice.message.content

        # Execute tool calls
        assistant_message = choice.message
        messages.append(assistant_message)

        for tool_call in assistant_message.tool_calls:
            fn_name = tool_call.function.name
            fn_args = json.loads(tool_call.function.arguments)

            if fn_name in TOOL_FUNCTIONS:
                result = TOOL_FUNCTIONS[fn_name](**fn_args)
            else:
                result = f"Error: Unknown tool '{fn_name}'"

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })

    return "Email agent reached maximum iterations without a final answer."
