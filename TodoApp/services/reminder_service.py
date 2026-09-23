import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.orm import Session
from TodoApp.models import Todos, Users
from TodoApp.services.email_service import send_deadline_email

logger = logging.getLogger("reminder_service")

def to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def is_deadline_approaching(deadline: Optional[datetime], now: Optional[datetime] = None) -> bool:
    if deadline is None:
        return False
    
    if now is None:
        now = datetime.now(timezone.utc)

    now_utc = to_utc(now)
    deadline_utc = to_utc(deadline)
    one_hour_later = now_utc + timedelta(hours=1)

    return now_utc <= deadline_utc <= one_hour_later

def process_reminders(db: Session, current_time: Optional[datetime] = None) -> int:
    logger.info("Checking deadline reminders...")

    now = current_time if current_time is not None else datetime.now(timezone.utc)
    now_utc = to_utc(now)
    one_hour_later_utc = now_utc + timedelta(hours=1)

    now_naive = now_utc.replace(tzinfo=None)
    one_hour_later_naive = one_hour_later_utc.replace(tzinfo=None)

    todos_to_check = (
        db.query(Todos)
        .filter(
            Todos.deadline.isnot(None),
            Todos.mail_sent == False,
            Todos.deadline >= now_naive,
            Todos.deadline <= one_hour_later_naive
        )
        .all()
    )

    sent_count = 0
    for todo in todos_to_check:
        if not is_deadline_approaching(todo.deadline, now_utc):
            continue

        owner = db.query(Users).filter(Users.id == todo.owner_id).first()
        if not owner or not owner.email or not owner.email.strip():
            logger.warning(f"No valid owner/email found for Todo {todo.id} (owner_id: {todo.owner_id}). Skipping.")
            continue

        try:
            email_sent = send_deadline_email(
                to_email=owner.email.strip(),
                todo_id=todo.id,
                title=todo.title,
                description=todo.description,
                deadline=todo.deadline
            )
        except Exception as e:
            logger.error(f"Unexpected error executing send_deadline_email for Todo {todo.id}: {e}")
            email_sent = False

        if email_sent:
            todo.mail_sent = True
            try:
                db.commit()
                sent_count += 1
                logger.info(f"Successfully marked mail_sent=True in DB for Todo {todo.id}.")
            except Exception as e:
                db.rollback()
                logger.error(f"Database commit failed after sending email for Todo {todo.id}: {e}")
        else:
            db.rollback()
            logger.warning(f"Email delivery failed for Todo {todo.id}. mail_sent remains False.")

    return sent_count
