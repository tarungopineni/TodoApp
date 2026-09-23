from .utils import *
from TodoApp.routers.auth import *
from fastapi import status
from jose import jwt
import pytest
from fastapi import HTTPException

app.dependency_overrides[get_db] = override_get_db

def test_authenticate_user(test_user):
    db = TestingSessionLocal()
    authenticated_user = authenticate(test_user.username,"Tarun@123",db)
    assert authenticated_user is not None
    assert authenticated_user.username == test_user.username
    non_existing_user = authenticate("wrong","worng",db)
    assert non_existing_user is None

def test_create_access_token():
    token = create_access_token(username = "example",user_id = 1,role = "admin",expires_delta = timedelta(minutes=20))
    response = jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM],options={"verify_signature":False})
    assert response["sub"] == "example"
    assert response["id"] == 1
    assert response["role"] == "admin"

@pytest.mark.asyncio
async def test_get_current_user():
    encode = {
        "sub":"Tarungopineni",
        "id":1,
        "role":"admin"
    }
    token = jwt.encode(encode,SECRET_KEY,ALGORITHM)
    response = await get_current_user(token)
    assert response["username"] == "Tarungopineni"
    assert response["id"] == 1
    assert response["user_role"] == "admin"

@pytest.mark.asyncio
async def test_get_current_user_missing_payload():
    encode = {"role":"user"}
    token = jwt.encode(encode,SECRET_KEY,ALGORITHM)
    with pytest.raises(HTTPException) as excinfo:
        await get_current_user(token)

    assert excinfo.value.status_code == 401
    assert excinfo.value.detail == "Could not validate user"