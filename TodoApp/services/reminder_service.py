import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from TodoApp.models import Todos, Users
from TodoApp.services.email_service import send_deadline_email

logger = logging.getLogger(__name__)

def to_utc(dt: datetime) -> datetime:
    """Converts any datetime (offset-naive or offset-aware) to timezone-aware UTC datetime."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def is_deadline_approaching(deadline: datetime, window_hours: float = 1.0) -> bool:
    """
    Returns True if deadline is not None and falls within:
    now <= deadline <= now + window_hours
    """
    if deadline is None:
        return False
    now = datetime.now(timezone.utc)
    deadline_utc = to_utc(deadline)
    window_end = now + timedelta(hours=window_hours)
    return now <= deadline_utc <= window_end

def check_and_send_immediate_reminder(db: Session, todo: Todos) -> bool:
    """
    Checks if a newly created or updated Todo is eligible for immediate email reminder.
    Sends email immediately if eligible and mail_sent is False.
    Does NOT fail or raise exception if email sending fails.
    Returns True if email was sent, False otherwise.
    """
    if todo is None or todo.deadline is None:
        return False

    logger.info(f"Immediate reminder check for todo {todo.id}")

    if todo.mail_sent:
        logger.info(f"Immediate reminder check for todo {todo.id}: mail_sent is already true, skipping.")
        return False

    if not is_deadline_approaching(todo.deadline):
        logger.info(f"Immediate reminder check for todo {todo.id}: Deadline is outside reminder window.")
        return False

    logger.info(f"Deadline is within 1 hour for todo {todo.id}")

    owner = db.query(Users).filter(Users.id == todo.owner_id).first()
    owner_email = owner.email if owner else None

    if not owner_email:
        logger.error(f"Cannot send reminder email for todo {todo.id}: Owner user ID {todo.owner_id} not found or missing email.")
        return False

    logger.info(f"Sending reminder email for todo {todo.id} to {owner_email}")
    try:
        success = send_deadline_email(
            to_email=owner_email,
            title=todo.title,
            deadline=todo.deadline,
            todo_id=todo.id,
            description=todo.description
        )

        if success:
            todo.mail_sent = True
            db.commit()
            logger.info(f"Reminder email sent successfully")
            logger.info(f"mail_sent=true for todo {todo.id}")
            return True
        else:
            db.rollback()
            logger.error(f"Failed to send reminder email for todo {todo.id}")
            return False
    except Exception as e:
        db.rollback()
        logger.error(f"Email sending failed for todo {todo.id}: {e}", exc_info=True)
        return False

def process_reminders(db: Session):
    """
    Queries for pending todos with deadlines approaching within 1 hour that have not received reminder emails.
    Sends reminder emails and updates `mail_sent = True` ONLY upon successful email delivery.
    """
    logger.info("Reminder check started")
    now_utc = datetime.now(timezone.utc)
    window_end_utc = now_utc + timedelta(hours=1)

    # Compare naive UTC bounds for SQLite / Postgres compatibility
    now_naive = now_utc.replace(tzinfo=None)
    window_end_naive = window_end_utc.replace(tzinfo=None)

    eligible_todos = (
        db.query(Todos)
        .filter(
            Todos.mail_sent == False,
            Todos.deadline != None,
            Todos.deadline >= now_naive,
            Todos.deadline <= window_end_naive
        )
        .all()
    )

    logger.info(f"Found {len(eligible_todos)} eligible task(s)")

    for todo in eligible_todos:
        # Re-check mail_sent flag to avoid duplicate processing in concurrency
        if todo.mail_sent:
            continue

        owner = db.query(Users).filter(Users.id == todo.owner_id).first()
        owner_email = owner.email if owner else None

        if not owner_email:
            logger.error(f"Cannot send email for Todo ID {todo.id}: Owner email not found.")
            continue

        logger.info(f"Sending reminder email for todo {todo.id} to {owner_email}")
        try:
            success = send_deadline_email(
                to_email=owner_email,
                title=todo.title,
                deadline=todo.deadline,
                todo_id=todo.id,
                description=todo.description
            )

            if success:
                todo.mail_sent = True
                db.commit()
                logger.info(f"Reminder email sent successfully")
                logger.info(f"mail_sent=true for todo {todo.id}")
            else:
                db.rollback()
                logger.error(f"Email delivery failed for todo {todo.id}. mail_sent remains False.")
        except Exception as e:
            db.rollback()
            logger.error(f"Exception while sending reminder for todo {todo.id}: {e}", exc_info=True)
