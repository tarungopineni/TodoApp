from ..models import Todos
from pydantic import BaseModel
from typing import Annotated, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import Depends,HTTPException,Path,APIRouter
from pydantic import Field
from ..database import SessionLocal
from starlette import status
from .auth import get_current_user

router = APIRouter(
    prefix = "/todos",
    tags = ['todos']
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session,Depends(get_db)]
user_dependency = Annotated[dict,Depends(get_current_user)]

class TodoRequest(BaseModel):
    title:str = Field(min_length=3)
    description:str = Field(min_length=3,max_length=20)
    priority:int = Field(gt=0)
    complete:bool
    task_datetime: Optional[datetime] = None
    deadline: Optional[datetime] = None

@router.get("/")
async def read_all(user:user_dependency,db:db_dependency,status_code=status.HTTP_200_OK):
    if user is None:
        raise HTTPException(status_code=401,detail = "Authentication failed!!")
    return db.query(Todos).filter(Todos.owner_id == user.get("id")).all()

@router.get("/todo/{todo_id}",status_code=status.HTTP_200_OK)
async def get_todo(user:user_dependency,db:db_dependency,todo_id:int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401,detail = "Authentication failed!!")
    todo_model = db.query(Todos).filter(Todos.id == todo_id).filter(Todos.owner_id == user.get("id")).first()
    if todo_model is not None:
        return todo_model
    raise HTTPException(status_code=404,detail="Todo with that id is not found")

@router.post("/todos",status_code=status.HTTP_201_CREATED)
async def create_todo(user:user_dependency,db:db_dependency,todo_request:TodoRequest):
    if user is None:
        raise HTTPException(status_code=401,detail = "Authentication failed!!")
    todo_model = Todos(**todo_request.model_dump(),owner_id = user.get("id"))
    db.add(todo_model)
    db.commit()
    return {"message":"todo created"}

@router.put("/todo/{todo_id}",status_code=status.HTTP_204_NO_CONTENT)
async def update_todo(user:user_dependency,db:db_dependency,todo_id:int,request:TodoRequest):
    if user is None:
        raise HTTPException(status_code=401,detail = "Authentication failed!!")
    todo_model = db.query(Todos).filter(Todos.id == todo_id).filter(Todos.owner_id == user.get("id")).first()
    if todo_model is None:
        raise HTTPException(status_code=404,detail="todo not found")
    todo_model.title = request.title
    todo_model.description = request.description
    todo_model.priority = request.priority
    todo_model.complete = request.complete
    todo_model.task_datetime = request.task_datetime
    todo_model.deadline = request.deadline
    db.commit()
    return {"message":"updated"}

@router.delete("/todo/{todo_id}",status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(user:user_dependency,db:db_dependency,todo_id:int):
    if user is None:
        raise HTTPException(status_code=401,detail = "Authentication failed!!")
    todo_model = db.query(Todos).filter(Todos.id == todo_id).filter(Todos.owner_id == user.get("id")).first()
    if todo_model is None:
        raise HTTPException(status_code=404,detail="model not found!!")
    db.query(Todos).filter(Todos.id == todo_id).delete()
    db.commit()
    return {"message","todo not found!!"}