from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from ..database import Base
from ..main import app
from ..routers.todos import get_db,get_current_user
from fastapi.testclient import TestClient
from fastapi import status

SQLALCHEMY_DATABASE_URL = "sqlite:///./testdb.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread":False},
    poolclass=StaticPool,
)

TestingLocalClient = sessionmaker(autoflush=False,autocommit = False,bind=engine)
Base.metadata.create_all(bind = engine)