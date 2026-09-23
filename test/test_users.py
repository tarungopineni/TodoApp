from .utils import *
from TodoApp.routers.users import get_db,get_current_user
from TodoApp.routers.auth import bcrypt_context
from fastapi import status

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user

def test_return_info(test_user):
    response = client.get("/user")
    assert response.status_code == 200
    assert response.json()["username"] == 'tarungopineni'
    assert response.json()["first_name"] == 'tarun'
    assert response.json()["last_name"] == 'gopineni'
    assert response.json()["role"] == 'dev'
    assert response.json()["phonenumber"] == '9573175753'

def test_password_change(test_user):
    response = client.put("/user/password",json={"password":"Tarun@123","new_password":"Tarun@123"})
    assert response.status_code == 204

def test_password_invalid_current_password(test_user):
    response = client.put("/user/password",json={"password":"old","new_password":"new"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail":"Old password does not match!!"}

def test_phonenumber_change(test_user):
    response = client.put("/user/add_phone/9573175753")
    assert response.status_code == 204