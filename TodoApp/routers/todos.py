from ..models import Todos
from pydantic import BaseModel
from typing import Annotated, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, Path, APIRouter
from pydantic import Field
from ..database import SessionLocal
from starlette import status
from .auth import get_current_user
from TodoApp.services.reminder_service import check_and_send_immediate_reminder, to_utc, is_deadline_approaching

router = APIRouter(
    prefix="/todos",
    tags=['todos']
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

class TodoRequest(BaseModel):
    title: str = Field(min_length=3)
    description: str = Field(min_length=3, max_length=100)
    priority: int = Field(gt=0)
    complete: bool
    task_datetime: Optional[datetime] = None
    deadline: Optional[datetime] = None

def validate_todo_datetimes(task_dt: Optional[datetime], deadline_dt: Optional[datetime]):
    now = datetime.now(timezone.utc)

    if task_dt is not None:
        if to_utc(task_dt) < now:
            raise HTTPException(status_code=400, detail="Start time cannot be in the past.")

    if deadline_dt is not None:
        if to_utc(deadline_dt) < now:
            raise HTTPException(status_code=400, detail="Deadline cannot be in the past.")

    if task_dt is not None and deadline_dt is not None:
        if to_utc(deadline_dt) < to_utc(task_dt):
            raise HTTPException(status_code=400, detail="Deadline cannot be before the task start time.")

def is_same_datetime(dt1: Optional[datetime], dt2: Optional[datetime]) -> bool:
    if dt1 is None and dt2 is None:
        return True
    if dt1 is None or dt2 is None:
        return False
    return to_utc(dt1) == to_utc(dt2)

@router.get("/")
async def read_all(user: user_dependency, db: db_dependency, status_code=status.HTTP_200_OK):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication failed!!")
    return db.query(Todos).filter(Todos.owner_id == user.get("id")).all()

@router.get("/todo/{todo_id}", status_code=status.HTTP_200_OK)
async def get_todo(user: user_dependency, db: db_dependency, todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication failed!!")
    todo_model = db.query(Todos).filter(Todos.id == todo_id).filter(Todos.owner_id == user.get("id")).first()
    if todo_model is not None:
        return todo_model
    raise HTTPException(status_code=404, detail="Todo with that id is not found")

@router.post("/todos", status_code=status.HTTP_201_CREATED)
async def create_todo(user: user_dependency, db: db_dependency, todo_request: TodoRequest):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication failed!!")
    validate_todo_datetimes(todo_request.task_datetime, todo_request.deadline)
    todo_model = Todos(**todo_request.model_dump(), owner_id=user.get("id"))
    db.add(todo_model)
    db.commit()
    db.refresh(todo_model)

    # Check and send immediate email if deadline is within 1 hour
    check_and_send_immediate_reminder(db, todo_model)

    return {"message": "todo created"}

@router.put("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_todo(user: user_dependency, db: db_dependency, todo_id: int, request: TodoRequest):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication failed!!")
    validate_todo_datetimes(request.task_datetime, request.deadline)
    todo_model = db.query(Todos).filter(Todos.id == todo_id).filter(Todos.owner_id == user.get("id")).first()
    if todo_model is None:
        raise HTTPException(status_code=404, detail="todo not found")

    old_deadline = todo_model.deadline
    deadline_changed = not is_same_datetime(old_deadline, request.deadline)

    todo_model.title = request.title
    todo_model.description = request.description
    todo_model.priority = request.priority
    todo_model.complete = request.complete
    todo_model.task_datetime = request.task_datetime
    todo_model.deadline = request.deadline

    # If deadline has changed, reset mail_sent flag so new deadline can generate a new reminder if needed
    if deadline_changed:
        todo_model.mail_sent = False

    db.commit()
    db.refresh(todo_model)

    # Check immediate reminder eligibility
    check_and_send_immediate_reminder(db, todo_model)

    return {"message": "updated"}

@router.delete("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(user: user_dependency, db: db_dependency, todo_id: int):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication failed!!")
    todo_model = db.query(Todos).filter(Todos.id == todo_id).filter(Todos.owner_id == user.get("id")).first()
    if todo_model is None:
        raise HTTPException(status_code=404, detail="model not found!!")
    db.query(Todos).filter(Todos.id == todo_id).delete()
    db.commit()
    return {"message": "todo deleted"}
