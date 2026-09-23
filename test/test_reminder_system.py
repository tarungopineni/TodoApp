import os
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from TodoApp.models import Todos, Users
from TodoApp.services.reminder_service import process_reminders
from TodoApp.services.email_service import is_email_configured, send_deadline_email
from TodoApp.scheduler.reminder_scheduler import ReminderScheduler
from test.utils import TestingSessionLocal, override_get_db, override_get_current_user, client, app

@pytest.fixture
def setup_user_and_todos():
    db = TestingSessionLocal()
    # Create test user
    user = Users(
        id=10,
        username="reminder_user",
        email="reminder_user@example.com",
        first_name="Reminder",
        last_name="User",
        hashed_password="hashed_pw",
        is_active=True,
        role="user"
    )
    db.add(user)
    db.commit()

    now = datetime.now()

    # 1. Todo with deadline > 1 hour away
    todo_far = Todos(
        id=101,
        title="Far Deadline Task",
        description="Deadline in 2 hours",
        priority=1,
        complete=False,
        owner_id=10,
        deadline=now + timedelta(hours=2),
        mail_sent=False
    )

    # 2. Todo with deadline within 1 hour
    todo_soon = Todos(
        id=102,
        title="Soon Deadline Task",
        description="Deadline in 30 minutes",
        priority=1,
        complete=False,
        owner_id=10,
        deadline=now + timedelta(minutes=30),
        mail_sent=False
    )

    # 3. Todo with expired deadline
    todo_expired = Todos(
        id=103,
        title="Expired Task",
        description="Deadline in past",
        priority=1,
        complete=False,
        owner_id=10,
        deadline=now - timedelta(minutes=30),
        mail_sent=False
    )

    # 4. Todo with mail_sent=True (already notified)
    todo_sent = Todos(
        id=104,
        title="Already Sent Task",
        description="Deadline in 30 mins but mail_sent=True",
        priority=1,
        complete=False,
        owner_id=10,
        deadline=now + timedelta(minutes=30),
        mail_sent=True
    )

    db.add_all([todo_far, todo_soon, todo_expired, todo_sent])
    db.commit()

    yield db

    db.query(Todos).filter(Todos.owner_id == 10).delete()
    db.query(Users).filter(Users.id == 10).delete()
    db.commit()
    db.close()


def test_deadline_more_than_one_hour_away_no_email(setup_user_and_todos):
    db = setup_user_and_todos
    now = datetime.now()
    with patch("TodoApp.services.reminder_service.send_deadline_email") as mock_send:
        mock_send.return_value = True
        process_reminders(db, current_time=now)
        sent_todo_ids = [call.kwargs.get('todo_id') if 'todo_id' in call.kwargs else call.args[1] for call in mock_send.call_args_list]
        assert 101 not in sent_todo_ids


def test_deadline_within_one_hour_email_attempted(setup_user_and_todos):
    db = setup_user_and_todos
    now = datetime.now()
    with patch("TodoApp.services.reminder_service.send_deadline_email") as mock_send:
        mock_send.return_value = True
        process_reminders(db, current_time=now)
        sent_todo_ids = [call.kwargs.get('todo_id') if 'todo_id' in call.kwargs else call.args[1] for call in mock_send.call_args_list]
        assert 102 in sent_todo_ids


def test_expired_deadline_no_email(setup_user_and_todos):
    db = setup_user_and_todos
    now = datetime.now()
    with patch("TodoApp.services.reminder_service.send_deadline_email") as mock_send:
        mock_send.return_value = True
        process_reminders(db, current_time=now)
        sent_todo_ids = [call.kwargs.get('todo_id') if 'todo_id' in call.kwargs else call.args[1] for call in mock_send.call_args_list]
        assert 103 not in sent_todo_ids


def test_mail_sent_true_no_email(setup_user_and_todos):
    db = setup_user_and_todos
    now = datetime.now()
    with patch("TodoApp.services.reminder_service.send_deadline_email") as mock_send:
        mock_send.return_value = True
        process_reminders(db, current_time=now)
        sent_todo_ids = [call.kwargs.get('todo_id') if 'todo_id' in call.kwargs else call.args[1] for call in mock_send.call_args_list]
        assert 104 not in sent_todo_ids


def test_successful_email_updates_mail_sent_to_true(setup_user_and_todos):
    db = setup_user_and_todos
    now = datetime.now()
    with patch("TodoApp.services.reminder_service.send_deadline_email") as mock_send:
        mock_send.return_value = True
        process_reminders(db, current_time=now)

        todo_soon = db.query(Todos).filter(Todos.id == 102).first()
        assert todo_soon.mail_sent is True


def test_failed_email_leaves_mail_sent_false(setup_user_and_todos):
    db = setup_user_and_todos
    now = datetime.now()
    with patch("TodoApp.services.reminder_service.send_deadline_email") as mock_send:
        mock_send.return_value = False
        process_reminders(db, current_time=now)

        todo_soon = db.query(Todos).filter(Todos.id == 102).first()
        assert todo_soon.mail_sent is False


def test_scheduler_email_failure_does_not_crash_fastapi():
    scheduler = ReminderScheduler(interval_seconds=60)
    with patch("TodoApp.scheduler.reminder_scheduler.process_reminders") as mock_proc:
        mock_proc.side_effect = Exception("SMTP Connection Failed!")
        scheduler._execute_check()  # Must catch exception safely without raising


def test_normal_api_endpoints_work_while_scheduler_running():
    response = client.get("/healthy")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
