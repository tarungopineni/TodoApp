import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional

logger = logging.getLogger("email_service")

def is_email_configured() -> bool:
    host = os.getenv("SMTP_HOST")
    port = os.getenv("SMTP_PORT")
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    from_email = os.getenv("SMTP_FROM_EMAIL")
    return bool(host and port and username and password and from_email)

def send_deadline_email(
    to_email: str,
    todo_id: int,
    title: str,
    description: Optional[str],
    deadline: datetime
) -> bool:
    if not is_email_configured():
        logger.warning(f"Email reminders disabled: SMTP configuration is incomplete. Skipping email for Todo {todo_id}.")
        return False

    host = os.getenv("SMTP_HOST")
    port_str = os.getenv("SMTP_PORT", "587")
    try:
        port = int(port_str)
    except ValueError:
        port = 587

    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    from_email = os.getenv("SMTP_FROM_EMAIL")
    use_tls_str = os.getenv("SMTP_USE_TLS", "true").lower()
    use_tls = use_tls_str in ("true", "1", "t", "yes")
    use_ssl_str = os.getenv("SMTP_USE_SSL", "false").lower()
    use_ssl = use_ssl_str in ("true", "1", "t", "yes")

    subject = f"Task Deadline Approaching: {title}"
    desc_str = description if description else ""
    body = (
        f"Your task deadline is approaching.\n\n"
        f"Task: {title}\n\n"
        f"Description:\n{desc_str}\n\n"
        f"Deadline:\n{deadline}\n\n"
        f"Please complete the task before the deadline."
    )

    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    logger.info(f"Sending deadline reminder for Todo {todo_id}.")
    try:
        if use_ssl or port == 465:
            server = smtplib.SMTP_SSL(host, port, timeout=10)
        else:
            server = smtplib.SMTP(host, port, timeout=10)
            if use_tls:
                server.starttls()

        server.login(username, password)
        server.send_message(msg)
        server.quit()
        logger.info(f"Deadline reminder sent successfully for Todo {todo_id}.")
        return True
    except Exception as e:
        logger.error(f"Failed to send deadline reminder for Todo {todo_id}: {e}")
        return False
