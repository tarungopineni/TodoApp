import sys
import time
import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from alembic.config import Config
from alembic import command

from .routers import auth, todos, admin, users
from .database import engine
from .models import Base
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from TodoApp.scheduler.reminder_scheduler import reminder_scheduler
from TodoApp.services.email_service import log_smtp_configuration

load_dotenv()

# Configure standard logging for production stdout/stderr
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger("api.request")

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        method = request.method
        path = request.url.path

        logger.info(f"API request {method} {path}")

        try:
            response = await call_next(request)
            process_time = (time.perf_counter() - start_time) * 1000
            logger.info(f"API response {method} {path} -> {response.status_code} ({process_time:.0f}ms)")
            return response
        except Exception as e:
            process_time = (time.perf_counter() - start_time) * 1000
            logger.error(f"API response {method} {path} -> 500 ERROR ({process_time:.0f}ms): {e}")
            raise e

def run_db_migrations():
    """Run Alembic database migrations automatically on startup."""
    try:
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        logging.getLogger(__name__).info("Alembic database migrations applied successfully (head revision).")
    except Exception as e:
        logging.getLogger(__name__).warning(f"Alembic auto-migration warning/notice: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    log_smtp_configuration()
    run_db_migrations()
    reminder_scheduler.start()
    yield
    await reminder_scheduler.stop()

app = FastAPI(lifespan=lifespan)

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="TodoApp/templates")
app.mount("/static", StaticFiles(directory="TodoApp/static"), name="static")

@app.get("/login-page")
def test(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/register-page")
def test(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/healthy")
async def health_check():
    return {"status": "healthy"}

app.include_router(auth.router)
app.include_router(todos.router)
app.include_router(admin.router)
app.include_router(users.router)
