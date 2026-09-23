from TodoApp.routers.todos import get_db,get_current_user
from fastapi import status
from TodoApp.models import Todos
from .utils import *
from datetime import datetime

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user

def test_read_all_authenticated(test_todo):
    response = client.get("/todos")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [{"id":1,"title":"learn coding","description":"learn everyday","complete":False,"owner_id":1,"priority":5,"task_datetime":None,"deadline":None,"mail_sent":False}]

def test_read_one_authenticated(test_todo):
    response = client.get("/todos/todo/1")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"id":1,"title":"learn coding","description":"learn everyday","complete":False,"owner_id":1,"priority":5,"task_datetime":None,"deadline":None,"mail_sent":False}

def test_read_one_authenticated_not_found():
    response = client.get("/todos/todo/999")
    assert response.status_code == 404
    assert response.json() == {'detail':'Todo with that id is not found'}

def test_create_todo(test_todo):
    request_data = {
        'title':"New Todo!",
        "description":"New todo description",
        "priority":5,
        "complete":False,
    }
    response = client.post('/todos/todos',json=request_data)
    assert response.status_code == 201
    db = TestingSessionLocal()
    model = db.query(Todos).filter(Todos.id == 2).first()
    assert model.title == request_data.get("title")
    assert model.description == request_data.get("description")
    assert model.priority == request_data.get("priority")
    assert model.complete == request_data.get("complete")

def test_create_todo_with_datetime_and_deadline(test_todo):
    dt_str = "2026-10-01T10:00:00"
    dl_str = "2026-10-05T18:00:00"
    request_data = {
        'title':"New Todo!",
        "description":"New todo description",
        "priority":5,
        "complete":False,
        "task_datetime": dt_str,
        "deadline": dl_str
    }
    response = client.post('/todos/todos',json=request_data)
    assert response.status_code == 201
    db = TestingSessionLocal()
    model = db.query(Todos).filter(Todos.id == 2).first()
    assert model.title == request_data.get("title")
    assert model.task_datetime is not None
    assert model.deadline is not None

def test_update_todo(test_todo):
    request_data = {
        "title" : "Change the title of the todo already saved!",
        "description" : "learn everyday",
        "priority" : 5,
        "complete" : False,
        "owner_id" : 1,
    }
    response = client.put("/todos/todo/1",json=request_data)
    assert response.status_code == 204
    db = TestingSessionLocal()
    model = db.query(Todos).filter(Todos.id == 1).first()
    assert model.title == "Change the title of the todo already saved!"

def test_update_todo_with_datetime_and_deadline(test_todo):
    dt_str = "2026-10-01T10:00:00"
    dl_str = "2026-10-05T18:00:00"
    request_data = {
        "title" : "Updated title with datetime",
        "description" : "learn everyday",
        "priority" : 5,
        "complete" : True,
        "task_datetime": dt_str,
        "deadline": dl_str
    }
    response = client.put("/todos/todo/1",json=request_data)
    assert response.status_code == 204
    db = TestingSessionLocal()
    model = db.query(Todos).filter(Todos.id == 1).first()
    assert model.title == "Updated title with datetime"
    assert model.complete is True
    assert model.task_datetime is not None
    assert model.deadline is not None

def test_update_todo_not_found(test_todo):
    request_data = {
        "title" : "Change the title of the todo already saved!",
        "description" : "learn everyday",
        "priority" : 5,
        "complete" : False,
        "owner_id" : 1,
    }
    response = client.put("/todos/todo/999",json=request_data)
    assert response.status_code == 404
    assert response.json() == {"detail":"todo not found"}

def test_delete_todo(test_todo):
    response = client.delete('/todos/todo/1')
    db = TestingSessionLocal()
    model = db.query(Todos).filter(Todos.id == 1).first()
    assert model is None
    assert response.status_code == 204

def test_delete_todo_not_found(test_todo):
    response = client.delete('/todos/todo/999')
    assert response.status_code == 404
    assert response.json() == {"detail":"model not found!!"}