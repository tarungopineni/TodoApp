from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from TodoApp.database import Base,SessionLocal
from sqlalchemy.orm import sessionmaker
from TodoApp.main import app
import pytest
from TodoApp.models import Todos,Users
from sqlalchemy import text
from fastapi.testclient import TestClient
from TodoApp.routers.auth import bcrypt_context

SQLALCHEMY_DATABASE_URL = "sqlite:///./testdb.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread":False},
    poolclass=StaticPool,
)

Base.metadata.drop_all(bind=engine)

TestingSessionLocal = sessionmaker(autocommit = False,autoflush=False,bind=engine)
Base.metadata.create_all(bind=engine)
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def override_get_current_user():
    return {"username":"testusername","id":1,"user_role":"admin"}

@pytest.fixture
def test_todo():
    todo = Todos(
        title = "learn coding",
        description = "learn everyday",
        priority = 5,
        complete = False,
        owner_id = 1,
    )
    db = TestingSessionLocal()
    db.add(todo)
    db.commit()
    yield todo
    with engine.connect() as connection:
        connection.execute(text("DELETE FROM todos;"))
        connection.commit()

@pytest.fixture
def test_user():
    user = Users(
        id = 1,
        username = "tarungopineni",
        email = "tarungopineni@gmail.com",
        first_name = "tarun",
        last_name = "gopineni",
        hashed_password = bcrypt_context.hash("Tarun@123"),
        is_active = True,
        role = "dev",
        phonenumber = "9573175753"
    )
    db = TestingSessionLocal()
    db.add(user)
    db.commit()
    yield user
    with engine.connect() as connection:
        connection.execute(text("DELETE FROM users;"))
        connection.commit()

client = TestClient(app)