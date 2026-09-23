from fastapi import APIRouter
from ..models import Users
from pydantic import BaseModel
from passlib.context import CryptContext
from typing import Annotated
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException,Request
from ..database import SessionLocal
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from datetime import timedelta, datetime, timezone
from starlette import status
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import IntegrityError

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')
db_dependency = Annotated[Session, Depends(get_db)]
SECRET_KEY = 'QWER234DFG456CVBN543'
ALGORITHM = 'HS256'
templates = Jinja2Templates(directory="TodoApp/templates")

### pages ###
@router.get("/login-page")
def render_login_page(request:Request):
    return templates.TemplateResponse("login.html",{"request":request})

@router.get("/register-page")
def render_login_page(request:Request):
    return templates.TemplateResponse("register.html",{"request":request})

### Endpoints ##

def authenticate(username, password, db):
    model = db.query(Users).filter(Users.username == username).first()
    if model is None:
        return None
    if not bcrypt_context.verify(password,model.hashed_password):
        return None
    return model

def create_access_token(username: str,user_id: int,role: str,expires_delta: timedelta):
    encode = {
        "sub": username,
        "id": user_id,
        "role": role
    }
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({"exp": expires})
    return jwt.encode(
        encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        username = payload.get("sub")
        user_id = payload.get("id")
        user_role = payload.get("role")
        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Could not validate user")
        return {
            "username": username,
            "id": user_id,
            "user_role": user_role
        }
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Could not validate user")
    
class User_Request(BaseModel):
    email: str
    username: str
    first_name: str
    last_name: str
    role: str
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency, Req: User_Request):

    # Check if username already exists
    existing_username = db.query(Users).filter(
        Users.username == Req.username
    ).first()

    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists"
        )

    # Check if email already exists
    existing_email = db.query(Users).filter(
        Users.email == Req.email
    ).first()

    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists"
        )

    # Hash password
    hashed_password = bcrypt_context.hash(Req.hashed_password)

    # Create user
    final_model = Users(
        email=Req.email,
        username=Req.username,
        first_name=Req.first_name,
        last_name=Req.last_name,
        role=Req.role,
        hashed_password=hashed_password
    )

    try:
        db.add(final_model)
        db.commit()
        db.refresh(final_model)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already exists"
        )

    return {
        "message": "User created successfully"
    }

@router.post("/token")
async def login(db: db_dependency,form_data: Annotated[OAuth2PasswordRequestForm,Depends()]):
    user = authenticate(form_data.username,form_data.password,db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate"
        )
    token = create_access_token(
        user.username,
        user.id,
        user.role,
        timedelta(minutes=20)
    )
    return {
        "access_token": token,
        "token_type": "bearer"
    }