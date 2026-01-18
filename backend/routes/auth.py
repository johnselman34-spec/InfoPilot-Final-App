"""
InfoPilot Explorer - Authentication Routes
Register, login, logout, and user profile management
"""
from fastapi import APIRouter, HTTPException, Body, Depends
from typing import Dict
from datetime import datetime, timezone
import uuid
import os

from models.schemas import UserCreate, UserLogin, User
from utils.db import db
from utils.auth import hash_password, generate_token, get_current_user, require_user

# Admin setup secret key - read from environment
ADMIN_SETUP_SECRET_KEY = os.environ.get("ADMIN_SETUP_SECRET_KEY", "infopilot_setup_2024_bear")

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


@router.post("/setup-admin")
async def setup_admin(secret_key: str = Body(..., embed=True)):
    """One-time setup endpoint to create admin user in production database.
    Requires a secret key for security.
    """
    # Security check - use a secret key to prevent unauthorized access
    if secret_key != "infopilot_setup_2024_bear":
        raise HTTPException(status_code=403, detail="Invalid setup key")
    
    # Check if admin already exists
    admin = await db.users.find_one({"email": "admin@infopilot.com"})
    if admin:
        return {"message": "Admin user already exists", "email": "admin@infopilot.com"}
    
    # Create admin user
    admin_user = {
        "id": str(uuid.uuid4()),
        "email": "admin@infopilot.com",
        "username": "InfoPilotAdmin",
        "hashed_password": hash_password("admin123"),
        "is_admin": True,
        "is_paid": True,
        "subscription_active": True,
        "subscription_type": "yearly",
        "laughter_points": 1000,
        "easter_eggs_caught": 0,
        "wallet_balance": 0,
        "theme_settings": {"mode": "dark", "preset": "cosmic"},
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(admin_user)
    
    # Also create admin settings if not exists
    existing_settings = await db.admin_settings.find_one({"id": "admin_settings"})
    if not existing_settings:
        default_settings = {
            "id": "admin_settings",
            "collation_limit": 40,
            "max_category_depth": 100,
            "newsletter_times": ["05:42", "08:37", "16:41"],
            "newsletter_enabled": True,
            "search_results_per_page": 20,
            "unpaid_max_pages": 3,
            "subscription_price_monthly": 1.00,
            "subscription_price_yearly": 9.98,
            "upgrade_message": "🚨 Pay-as-you-go promotion is only while supplies last!",
            "phd_min_occurrences": 3,
            "phd_min_words": 1500,
            "personal_report_min_i": 3,
            "personal_report_min_words": 75,
            "banned_words": []
        }
        await db.admin_settings.insert_one(default_settings)
    
    return {
        "message": "Admin user created successfully!",
        "email": "admin@infopilot.com",
        "password": "admin123",
        "note": "Please change the password after first login"
    }

