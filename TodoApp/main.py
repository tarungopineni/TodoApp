from contextlib import asynccontextmanager
from fastapi import FastAPI,Request
from .routers import auth,todos,admin,users
from .database import engine
from .models import Base
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from TodoApp.scheduler.reminder_scheduler import reminder_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    reminder_scheduler.start()
    yield
    await reminder_scheduler.stop()

app = FastAPI(lifespan=lifespan)

Base.metadata.create_all(bind = engine)

templates = Jinja2Templates(directory="TodoApp/templates")
app.mount("/static",StaticFiles(directory="TodoApp/static"),name="static")

@app.get("/login-page")
def test(request:Request):
    return templates.TemplateResponse("home.html",{"request":request})

@app.get("/register-page")
def test(request:Request):
    return templates.TemplateResponse("register.html",{"request":request})

@app.get("/healthy")
async def health_check():
    return {"status":"healthy"}

app.include_router(auth.router) 
app.include_router(todos.router)
app.include_router(admin.router)
app.include_router(users.router)