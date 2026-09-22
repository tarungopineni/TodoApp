from .utils import *
from ..routers.admin import get_current_user,get_db
from ..main import app
from fastapi import status

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user

def test_read_all(test_todo):
    response = client.get("/admin/todo")
    assert response.status_code == 200
    assert response.json() == [{"id":1,"title" : "learn coding","description" : "learn everyday","priority" : 5,"complete" : False,"owner_id" : 1,"task_datetime": None, "deadline": None}]

def test_admin_delete_todo(test_todo):
    response = client.delete('/admin/todo/1')
    assert response.status_code == 204
    db = TestingSessionLocal()
    model = db.query(Todos).filter(Todos.id == 1).first()
    assert model is None

def test_admin_delete_todo_not_found():
    response = client.delete('/admin/todo/9999')
    assert response.status_code == 404
    assert response.json() == {"detail":"could not found todo"}