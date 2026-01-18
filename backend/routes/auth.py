"""
InfoPilot Explorer - Authentication Routes
Register, login, logout, and user profile management
"""
from fastapi import APIRouter, HTTPException, Body, Depends
from typing import Dict
from datetime import datetime, timezone
import uuid

from models.schemas import UserCreate, UserLogin, User
from utils.db import db
from utils.auth import hash_password, generate_token, get_current_user, require_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register")
async def register(user_data: UserCreate):
    """Register a new user."""
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    existing_username = await db.users.find_one({"username": user_data.username})
    if existing_username:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    user = User(
        email=user_data.email,
        username=user_data.username,
        first_name=user_data.first_name,
        last_name=user_data.last_name
    )
    user_dict = user.model_dump()
    user_dict["hashed_password"] = hash_password(user_data.password)
    
    await db.users.insert_one(user_dict)
    
    # Create session
    token = generate_token()
    session = {
        "id": str(uuid.uuid4()),
        "user_id": user.id,
        "token": token,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.sessions.insert_one(session)
    
    return {"user": {k: v for k, v in user_dict.items() if k not in ["hashed_password", "_id"]}, "token": token}


@router.post("/login")
async def login(credentials: UserLogin):
    """Login with email and password."""
    user = await db.users.find_one({"email": credentials.email})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if user.get("hashed_password") != hash_password(credentials.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Delete old sessions
    await db.sessions.delete_many({"user_id": user["id"]})
    
    # Create new session
    token = generate_token()
    session = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "token": token,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.sessions.insert_one(session)
    
    return {"user": {k: v for k, v in user.items() if k not in ["hashed_password", "_id"]}, "token": token}


@router.get("/me")
async def get_me(user: Dict = Depends(require_user)):
    """Get current user profile."""
    return {k: v for k, v in user.items() if k != "_id"}


@router.post("/logout")
async def logout(user: Dict = Depends(require_user)):
    """Logout user."""
    await db.sessions.delete_many({"user_id": user["id"]})
    return {"message": "Logged out successfully"}
