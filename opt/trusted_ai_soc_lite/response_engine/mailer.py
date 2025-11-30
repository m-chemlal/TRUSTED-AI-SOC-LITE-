#!/usr/bin/env python3
"""Simple SMTP helper for SOC notifications."""
from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from typing import Optional

DEFAULT_SMTP_HOST = os.getenv("SOC_SMTP_HOST", "localhost")
DEFAULT_SMTP_PORT = int(os.getenv("SOC_SMTP_PORT", "25"))
DEFAULT_SMTP_USER = os.getenv("SOC_SMTP_USER")
DEFAULT_SMTP_PASSWORD = os.getenv("SOC_SMTP_PASSWORD")
DEFAULT_SMTP_STARTTLS = os.getenv("SOC_SMTP_STARTTLS", "0") == "1"
DEFAULT_SENDER = os.getenv("SOC_ALERT_SENDER", "soc-alert@trusted.ai")


def send_alert(
    recipient: str,
    subject: str,
    body: str,
    *,
    smtp_host: str = DEFAULT_SMTP_HOST,
    smtp_port: int = DEFAULT_SMTP_PORT,
    smtp_user: Optional[str] = DEFAULT_SMTP_USER,
    smtp_password: Optional[str] = DEFAULT_SMTP_PASSWORD,
    sender: str = DEFAULT_SENDER,
    starttls: bool = DEFAULT_SMTP_STARTTLS,
) -> None:
    """Send an alert email.

    The SMTP settings can be overridden per-call or via environment variables.
    The function is intentionally minimal to keep dependencies out of the
    response engine.
    """

    if not recipient:
        raise ValueError("recipient is required to send an alert email")

    message = EmailMessage()
    message["From"] = sender
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as smtp:
        if starttls:
            smtp.starttls()
        if smtp_user and smtp_password:
            smtp.login(smtp_user, smtp_password)
        smtp.send_message(message)


__all__ = ["send_alert"]
