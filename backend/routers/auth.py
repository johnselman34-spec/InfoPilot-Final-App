"""
Authentication routes for InfoPilot Explorer
"""
from fastapi import APIRouter, HTTPException, Request, Response, Depends
from datetime import datetime, timezone, timedelta
import httpx
import uuid
import logging

from services.database import db
from models.schemas import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


async def get_current_user(request: Request) -> User:
    """Get current authenticated user from session token"""
    session_token = request.cookies.get("session_token")
    
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = await db.user_sessions.find_one(
        {"session_token": session_token},
        {"_id": 0}
    )
    
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    # Check expiration
    expires_at = datetime.fromisoformat(session["expires_at"].replace("Z", "+00:00"))
    if datetime.now(timezone.utc) > expires_at:
        await db.user_sessions.delete_one({"session_token": session_token})
        raise HTTPException(status_code=401, detail="Session expired")
    
    user_doc = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=401, detail="User not found")
    
    return User(**user_doc)


async def require_auth(request: Request) -> User:
    """Dependency to require authentication"""
    return await get_current_user(request)


@router.post("/session")
async def create_session(request: Request, response: Response):
    """Create session from Emergent OAuth session_id"""
    data = await request.json()
    session_id = data.get("session_id")
    
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")
    
    # Exchange session_id for user data
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
                headers={"X-Session-ID": session_id}
            )
            if resp.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid session")
            
            user_data = resp.json()
        except Exception as e:
            logger.error(f"OAuth error: {e}")
            raise HTTPException(status_code=401, detail="Authentication failed")
    
    # Create or update user
    existing_user = await db.users.find_one({"email": user_data["email"]}, {"_id": 0})
    
    if existing_user:
        user_id = existing_user["user_id"]
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {
                "name": user_data["name"],
                "picture": user_data.get("picture")
            }}
        )
    else:
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        new_user = {
            "user_id": user_id,
            "email": user_data["email"],
            "name": user_data["name"],
            "picture": user_data.get("picture"),
            "is_paid": False,
            "is_admin": user_data["email"] == "jjspilot24@gmail.com",
            "xp": 0,
            "level": 1,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(new_user)
    
    # Create session
    session_token = user_data.get("session_token", f"sess_{uuid.uuid4().hex}")
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    await db.user_sessions.insert_one({
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    # Set cookie
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=7 * 24 * 60 * 60,
        path="/"
    )
    
    user_doc = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    return user_doc


@router.get("/me")
async def get_me(user: User = Depends(require_auth)):
    """Get current user"""
    return user.model_dump()


@router.post("/logout")
async def logout(request: Request, response: Response):
    """Logout user"""
    session_token = request.cookies.get("session_token")
    if session_token:
        await db.user_sessions.delete_one({"session_token": session_token})
    
    response.delete_cookie("session_token", path="/")
    return {"message": "Logged out"}
