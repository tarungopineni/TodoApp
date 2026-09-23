import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

logger = logging.getLogger(__name__)

def is_email_configured() -> bool:
    """
    Checks if SMTP host and username credentials are configured in .env.
    """
    host = os.getenv("SMTP_HOST", "").strip()
    username = os.getenv("SMTP_USERNAME", "").strip()
    password = os.getenv("SMTP_PASSWORD", "").strip()
    return bool(host and username and password)

def log_smtp_configuration() -> None:
    """
    Logs non-sensitive details about current SMTP settings at application startup.
    Never logs passwords.
    """
    host = os.getenv("SMTP_HOST", "").strip()
    port = os.getenv("SMTP_PORT", "587").strip()
    username = os.getenv("SMTP_USERNAME", "").strip()
    from_email = os.getenv("SMTP_FROM_EMAIL", "").strip()
    use_tls = os.getenv("SMTP_USE_TLS", "true").strip()
    use_ssl = os.getenv("SMTP_USE_SSL", "false").strip()

    logger.info("=== SMTP Configuration ===")
    logger.info(f"Host: {host if host else '[NOT CONFIGURED]'}")
    logger.info(f"Port: {port}")
    logger.info(f"From Email: {from_email if from_email else '[NOT CONFIGURED]'}")
    logger.info(f"Username: {username if username else '[NOT CONFIGURED]'}")
    logger.info(f"Use TLS: {use_tls}, Use SSL: {use_ssl}")
    logger.info("==========================")

def send_deadline_email(
    to_email: str,
    title: str,
    deadline,
    todo_id: int,
    description: str = None
) -> bool:
    """
    Sends a reminder email to `to_email` regarding a Todo task approaching its deadline.
    Returns True if sent successfully, False otherwise.
    """
    if not to_email:
        logger.error(f"Cannot send email for Todo {todo_id}: Owner has no email address.")
        return False

    host = os.getenv("SMTP_HOST", "").strip()
    port_str = os.getenv("SMTP_PORT", "587").strip()
    try:
        port = int(port_str)
    except ValueError:
        port = 587

    username = os.getenv("SMTP_USERNAME", "").strip()
    password = os.getenv("SMTP_PASSWORD", "").strip()
    from_email = os.getenv("SMTP_FROM_EMAIL", "").strip()
    use_tls_str = os.getenv("SMTP_USE_TLS", "true").lower().strip()
    use_tls = use_tls_str in ("true", "1", "t", "yes")
    use_ssl_str = os.getenv("SMTP_USE_SSL", "false").lower().strip()
    use_ssl = use_ssl_str in ("true", "1", "t", "yes")

    subject = f"Task deadline approaching: {title}"
    desc_str = description if description else "No description provided."
    deadline_str = deadline.isoformat() if hasattr(deadline, 'isoformat') else str(deadline)

    body = (
        f"Hello,\n\n"
        f"This is an automated reminder that your task deadline is approaching.\n\n"
        f"Task Title: {title}\n"
        f"Description: {desc_str}\n"
        f"Deadline: {deadline_str}\n\n"
        f"Please log in to your Todo application to complete or update this task.\n\n"
        f"Best regards,\n"
        f"Todo Task Master Team"
    )

    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    logger.info(f"Connecting to SMTP server {host}:{port} to send reminder for Todo {todo_id}.")
    try:
        if not host:
            logger.error(f"SMTP configuration error: SMTP_HOST is not configured in .env.")
            return False

        if use_ssl:
            server = smtplib.SMTP_SSL(host, port, timeout=10)
        else:
            server = smtplib.SMTP(host, port, timeout=10)

        if use_tls and not use_ssl:
            server.starttls()

        if username and password:
            server.login(username, password)

        server.send_message(msg)
        server.quit()
        logger.info(f"Successfully sent reminder email to {to_email} for Todo ID {todo_id}.")
        return True

    except Exception as e:
        logger.error(f"Failed to send email to {to_email} for Todo ID {todo_id}: {e}", exc_info=True)
        return False
