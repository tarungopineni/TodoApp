import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.orm import Session
from TodoApp.models import Todos, Users
from TodoApp.services.email_service import send_deadline_email

logger = logging.getLogger("reminder_service")

def is_deadline_approaching(deadline: Optional[datetime], now: Optional[datetime] = None) -> bool:
    """
    Checks if deadline is within [now, now + 1 hour].
    Handles both timezone-naive and timezone-aware datetimes safely.
    """
    if deadline is None:
        return False
    
    if now is None:
        now = datetime.now(deadline.tzinfo) if deadline.tzinfo is not None else datetime.now()
    else:
        # Align timezone awareness
        if deadline.tzinfo is not None and now.tzinfo is None:
            now = now.replace(tzinfo=deadline.tzinfo)
        elif deadline.tzinfo is None and now.tzinfo is not None:
            deadline = deadline.replace(tzinfo=now.tzinfo)

    one_hour_later = now + timedelta(hours=1)
    return now <= deadline <= one_hour_later

def process_reminders(db: Session, current_time: Optional[datetime] = None) -> int:
    """
    Queries tasks with a deadline within the next 1 hour that have not had email sent yet.
    Sends reminder emails and updates mail_sent=True upon success.
    Returns the count of successfully sent emails.
    """
    logger.info("Checking deadline reminders...")

    now = current_time if current_time is not None else datetime.now()
    one_hour_later = now + timedelta(hours=1)

    # Query tasks eligible for reminder from database
    todos_to_check = (
        db.query(Todos)
        .filter(
            Todos.deadline.isnot(None),
            Todos.mail_sent == False,
            Todos.deadline >= now,
            Todos.deadline <= one_hour_later
        )
        .all()
    )

    sent_count = 0
    for todo in todos_to_check:
        # Double check condition in Python for safety
        if not is_deadline_approaching(todo.deadline, now):
            continue

        owner = db.query(Users).filter(Users.id == todo.owner_id).first()
        if not owner or not owner.email:
            logger.warning(f"No valid owner/email found for Todo {todo.id} (owner_id: {todo.owner_id}). Skipping.")
            continue

        email_sent = send_deadline_email(
            to_email=owner.email,
            todo_id=todo.id,
            title=todo.title,
            description=todo.description,
            deadline=todo.deadline
        )

        if email_sent:
            todo.mail_sent = True
            try:
                db.commit()
                sent_count += 1
                logger.info(f"Successfully marked mail_sent=True for Todo {todo.id}.")
            except Exception as e:
                db.rollback()
                logger.error(f"Database update failed after sending email for Todo {todo.id}: {e}")
        else:
            logger.warning(f"Email delivery failed for Todo {todo.id}. mail_sent remains False.")

    return sent_count
