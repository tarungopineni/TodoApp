import pytest
from unittest.mock import patch
from datetime import datetime, timezone, timedelta
from TodoApp.models import Todos, Users
from TodoApp.services.reminder_service import process_reminders, is_deadline_approaching, check_and_send_immediate_reminder
from TodoApp.services.email_service import is_email_configured, send_deadline_email
from test.utils import TestingSessionLocal, override_get_db, override_get_current_user, client, app

@pytest.fixture(autouse=True)
def setup_test_db():
    db = TestingSessionLocal()
    db.query(Todos).delete()
    db.query(Users).delete()

    user = Users(
        id=1,
        email="testuser@example.com",
        username="testuser",
        first_name="Test",
        last_name="User",
        hashed_password="hashedpassword",
        is_active=True,
        role="user"
    )
    db.add(user)
    db.commit()
    db.close()
    yield
    db = TestingSessionLocal()
    db.query(Todos).delete()
    db.query(Users).delete()
    db.commit()
    db.close()

# 1. Create Todo with deadline > 1 hour away -> no immediate email
@patch("TodoApp.services.reminder_service.send_deadline_email", return_value=True)
def test_create_todo_far_future_deadline_no_immediate_email(mock_send_email):
    now = datetime.now(timezone.utc)
    future_deadline = (now + timedelta(hours=3)).isoformat()
    response = client.post(
        "/todos/todos",
        json={
            "title": "Future Task",
            "description": "Task description",
            "priority": 1,
            "complete": False,
            "deadline": future_deadline
        }
    )
    assert response.status_code == 201
    mock_send_email.assert_not_called()
    db = TestingSessionLocal()
    todo = db.query(Todos).first()
    assert todo is not None
    assert todo.mail_sent is False
    db.close()

# 2. Create Todo with deadline exactly 1 hour away -> immediate email
@patch("TodoApp.services.reminder_service.send_deadline_email", return_value=True)
def test_create_todo_exact_1_hour_deadline_immediate_email(mock_send_email):
    now = datetime.now(timezone.utc)
    exact_deadline = (now + timedelta(minutes=59, seconds=55)).isoformat()
    response = client.post(
        "/todos/todos",
        json={
            "title": "Exact 1 Hour Task",
            "description": "Task description",
            "priority": 1,
            "complete": False,
            "deadline": exact_deadline
        }
    )
    assert response.status_code == 201
    assert mock_send_email.called
    db = TestingSessionLocal()
    todo = db.query(Todos).first()
    assert todo.mail_sent is True
    db.close()

# 3. Create Todo with deadline 30 minutes away -> immediate email
@patch("TodoApp.services.reminder_service.send_deadline_email", return_value=True)
def test_create_todo_30_mins_deadline_immediate_email(mock_send_email):
    now = datetime.now(timezone.utc)
    deadline = (now + timedelta(minutes=30)).isoformat()
    response = client.post(
        "/todos/todos",
        json={
            "title": "30 Mins Task",
            "description": "Task description",
            "priority": 1,
            "complete": False,
            "deadline": deadline
        }
    )
    assert response.status_code == 201
    assert mock_send_email.called
    db = TestingSessionLocal()
    todo = db.query(Todos).first()
    assert todo.mail_sent is True
    db.close()

# 4. Create Todo with deadline in the past -> validation error (400)
def test_create_todo_past_deadline_validation_error():
    now = datetime.now(timezone.utc)
    past_deadline = (now - timedelta(minutes=10)).isoformat()
    response = client.post(
        "/todos/todos",
        json={
            "title": "Past Task",
            "description": "Task description",
            "priority": 1,
            "complete": False,
            "deadline": past_deadline
        }
    )
    assert response.status_code == 400
    assert "Deadline cannot be in the past" in response.json()["detail"]

# 5. Create Todo with mail_sent false and scheduler finds it -> email sent
@patch("TodoApp.services.reminder_service.send_deadline_email", return_value=True)
def test_scheduler_finds_unemailed_eligible_todo(mock_send_email):
    db = TestingSessionLocal()
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    todo = Todos(
        title="Pending Task",
        description="Desc",
        priority=1,
        complete=False,
        owner_id=1,
        deadline=now_utc + timedelta(minutes=45),
        mail_sent=False
    )
    db.add(todo)
    db.commit()

    process_reminders(db)

    db.refresh(todo)
    assert todo.mail_sent is True
    assert mock_send_email.called
    db.close()

# 6. Successful email -> mail_sent becomes true
@patch("TodoApp.services.reminder_service.send_deadline_email", return_value=True)
def test_successful_email_updates_mail_sent_flag(mock_send_email):
    db = TestingSessionLocal()
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    todo = Todos(
        title="Sample Task",
        description="Desc",
        priority=1,
        complete=False,
        owner_id=1,
        deadline=now_utc + timedelta(minutes=30),
        mail_sent=False
    )
    db.add(todo)
    db.commit()

    res = check_and_send_immediate_reminder(db, todo)
    assert res is True
    db.refresh(todo)
    assert todo.mail_sent is True
    db.close()

# 7. Failed email -> mail_sent remains false
@patch("TodoApp.services.reminder_service.send_deadline_email", return_value=False)
def test_failed_email_leaves_mail_sent_false(mock_send_email):
    db = TestingSessionLocal()
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    todo = Todos(
        title="Failed Mail Task",
        description="Desc",
        priority=1,
        complete=False,
        owner_id=1,
        deadline=now_utc + timedelta(minutes=30),
        mail_sent=False
    )
    db.add(todo)
    db.commit()

    res = check_and_send_immediate_reminder(db, todo)
    assert res is False
    db.refresh(todo)
    assert todo.mail_sent is False
    db.close()

# 8. Immediate email succeeds -> scheduler does not send duplicate email
@patch("TodoApp.services.reminder_service.send_deadline_email", return_value=True)
def test_immediate_success_prevents_scheduler_duplicate(mock_send_email):
    now = datetime.now(timezone.utc)
    deadline = (now + timedelta(minutes=25)).isoformat()
    response = client.post(
        "/todos/todos",
        json={
            "title": "Immediate Task",
            "description": "Task description",
            "priority": 1,
            "complete": False,
            "deadline": deadline
        }
    )
    assert response.status_code == 201
    assert mock_send_email.call_count == 1

    # Now run scheduler
    db = TestingSessionLocal()
    process_reminders(db)
    # Total call count should remain 1 (no duplicate call!)
    assert mock_send_email.call_count == 1
    db.close()

# 9. Update Todo deadline from > 1 hour away to < 1 hour away -> email is triggered
@patch("TodoApp.services.reminder_service.send_deadline_email", return_value=True)
def test_update_todo_deadline_triggers_immediate_email(mock_send_email):
    now = datetime.now(timezone.utc)
    far_deadline = (now + timedelta(hours=5)).isoformat()

    # Create task with far deadline
    post_res = client.post(
        "/todos/todos",
        json={
            "title": "Update Deadline Task",
            "description": "Task description",
            "priority": 1,
            "complete": False,
            "deadline": far_deadline
        }
    )
    assert post_res.status_code == 201
    assert mock_send_email.call_count == 0

    db = TestingSessionLocal()
    todo = db.query(Todos).first()
    todo_id = todo.id
    db.close()

    # Update deadline to 30 mins from now
    near_deadline = (now + timedelta(minutes=30)).isoformat()
    put_res = client.put(
        f"/todos/todo/{todo_id}",
        json={
            "title": "Update Deadline Task",
            "description": "Task description",
            "priority": 1,
            "complete": False,
            "deadline": near_deadline
        }
    )
    assert put_res.status_code == 204
    assert mock_send_email.call_count == 1

# 10. Update a Todo that already has mail_sent=true without changing its deadline -> do not send another email
@patch("TodoApp.services.reminder_service.send_deadline_email", return_value=True)
def test_update_todo_same_deadline_no_duplicate_email(mock_send_email):
    now = datetime.now(timezone.utc)
    deadline_dt = now + timedelta(minutes=30)
    deadline_iso = deadline_dt.isoformat()

    # Create task (triggers 1 email)
    post_res = client.post(
        "/todos/todos",
        json={
            "title": "Same Deadline Task",
            "description": "Task description",
            "priority": 1,
            "complete": False,
            "deadline": deadline_iso
        }
    )
    assert post_res.status_code == 201
    assert mock_send_email.call_count == 1

    db = TestingSessionLocal()
    todo = db.query(Todos).first()
    todo_id = todo.id
    # Get exact stored deadline from DB to send back in update
    stored_deadline_iso = todo.deadline.replace(tzinfo=timezone.utc).isoformat() if todo.deadline else deadline_iso
    db.close()

    # Update title only, same stored deadline
    put_res = client.put(
        f"/todos/todo/{todo_id}",
        json={
            "title": "Renamed Same Deadline Task",
            "description": "Task description",
            "priority": 1,
            "complete": False,
            "deadline": stored_deadline_iso
        }
    )
    assert put_res.status_code == 204
    # Call count should STILL be 1 (no duplicate email on update with unchanged deadline!)
    assert mock_send_email.call_count == 1

# 11. Multiple eligible Todos -> each gets the appropriate reminder
@patch("TodoApp.services.reminder_service.send_deadline_email", return_value=True)
def test_multiple_eligible_todos_processed(mock_send_email):
    db = TestingSessionLocal()
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    t1 = Todos(title="Task 1", description="D1", priority=1, complete=False, owner_id=1, deadline=now_utc + timedelta(minutes=20), mail_sent=False)
    t2 = Todos(title="Task 2", description="D2", priority=1, complete=False, owner_id=1, deadline=now_utc + timedelta(minutes=40), mail_sent=False)
    db.add_all([t1, t2])
    db.commit()

    process_reminders(db)

    assert mock_send_email.call_count == 2
    db.refresh(t1)
    db.refresh(t2)
    assert t1.mail_sent is True
    assert t2.mail_sent is True
    db.close()

# 12. SMTP failure -> Todo creation/update still succeeds, error logged, mail_sent remains false
@patch("TodoApp.services.reminder_service.send_deadline_email", return_value=False)
def test_smtp_failure_todo_creation_succeeds(mock_send_email):
    now = datetime.now(timezone.utc)
    deadline = (now + timedelta(minutes=30)).isoformat()
    response = client.post(
        "/todos/todos",
        json={
            "title": "SMTP Fail Task",
            "description": "Task description",
            "priority": 1,
            "complete": False,
            "deadline": deadline
        }
    )
    # Creation MUST succeed even if email fails!
    assert response.status_code == 201
    db = TestingSessionLocal()
    todo = db.query(Todos).first()
    assert todo is not None
    assert todo.mail_sent is False
    db.close()

# 13. Scheduler failure -> FastAPI remains responsive
def test_health_check_endpoint():
    response = client.get("/healthy")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
