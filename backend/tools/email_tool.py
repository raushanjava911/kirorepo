"""Tool: Send email via SMTP."""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "send_email",
        "description": "Send an email to a recipient. Use when the user asks to send, compose, or email someone. Requires recipient email address, subject, and body.",
        "parameters": {
            "type": "object",
            "properties": {
                "to": {
                    "type": "string",
                    "description": "Recipient email address, e.g. 'john@example.com'.",
                },
                "subject": {
                    "type": "string",
                    "description": "Email subject line.",
                },
                "body": {
                    "type": "string",
                    "description": "Email body content (plain text).",
                },
            },
            "required": ["to", "subject", "body"],
        },
    },
}


def send_email(to: str, subject: str, body: str) -> str:
    """Send an email using SMTP credentials from environment variables."""

    # Read SMTP config from environment
    smtp_host = os.environ.get("SMTP_HOST", "")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_password = os.environ.get("SMTP_PASSWORD", "")
    from_email = os.environ.get("FROM_EMAIL", smtp_user)

    if not smtp_host or not smtp_user or not smtp_password:
        return "Error: Email is not configured. Set SMTP_HOST, SMTP_USER, and SMTP_PASSWORD environment variables."

    try:
        # Build the email
        msg = MIMEMultipart()
        msg["From"] = from_email
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        # Send via SMTP
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)

        return f"Email sent successfully to {to} with subject: '{subject}'"

    except Exception as e:
        return f"Error sending email: {str(e)}"
