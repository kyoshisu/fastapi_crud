from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
import hashlib
import secrets
from app.database import get_db
from app.models import User
from typing import Dict

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password

active_sessions: Dict[str, int] = {}

router = APIRouter(prefix="/auth", tags=["Authentication"])

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str

def generate_token(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    active_sessions[token] = user_id
    return token

@router.post("/register", response_model=UserResponse)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()
    
    if existing_user:
        raise HTTPException(400, "Пользователь с таким username или email уже существует")
    
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hash_password(user_data.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return UserResponse(id=new_user.id, username=new_user.username, email=new_user.email)

@router.post("/login")
def login(user_data: UserLogin, db: Session = Depends(get_db), response: Response = None):
    user = db.query(User).filter(User.username == user_data.username).first()
    
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(401, "Неверное имя пользователя или пароль")
    
    token = generate_token(user.id)
    
    if response:
        response.set_cookie(key="session_token", value=token, httponly=True)
    
    return {"message": "Вход выполнен", "token": token, "user_id": user.id}

@router.post("/logout")
def logout(request: Request, response: Response):
    token = request.cookies.get("session_token")
    if token and token in active_sessions:
        del active_sessions[token]
    
    response.delete_cookie("session_token")
    return {"message": "Выход выполнен"}

def get_current_user_id(request: Request) -> int:
    token = request.cookies.get("session_token")
    if not token or token not in active_sessions:
        raise HTTPException(401, "Не авторизован")
    return active_sessions[token]