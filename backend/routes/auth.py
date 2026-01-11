"""
InfoPilot Explorer - Authentication Routes
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime
import re
import httpx

from config import db, logger
from models.schemas import UserCreate, UserLogin, GoogleAuthRequest
from services.auth_service import AuthService

router = APIRouter(tags=["Authentication"])
security = HTTPBearer(auto_error=False)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to get current authenticated user"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = credentials.credentials
    session = await db.sessions.find_one({
        "token": token,
        "expires_at": {"$gt": datetime.utcnow()}
    })
    
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    from bson import ObjectId
    user = await db.users.find_one({"_id": ObjectId(session["user_id"])})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user


async def get_optional_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to get current user if authenticated, None otherwise"""
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials)
    except:
        return None


@router.post("/auth/register", response_model=dict)
async def register(user: UserCreate):
    """Register a new user"""
    # Check if user exists (case-insensitive)
    existing = await db.users.find_one({
        "$or": [
            {"email": {"$regex": f"^{re.escape(user.email)}$", "$options": "i"}},
            {"username": user.username}
        ]
    })
    if existing:
        raise HTTPException(status_code=400, detail="Email or username already exists")
    
    # Create user
    new_user = await AuthService.create_user(
        email=user.email,
        username=user.username,
        password=user.password
    )
    
    # Create session
    token = await AuthService.create_session(str(new_user["_id"]))
    
    return {
        "token": token,
        "user": AuthService.format_user_response(new_user)
    }


@router.post("/auth/login", response_model=dict)
async def login(credentials: UserLogin):
    """Login with email and password"""
    # Case-insensitive email lookup
    user = await db.users.find_one({
        "email": {"$regex": f"^{re.escape(credentials.email)}$", "$options": "i"}
    })
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not user.get("hashed_password"):
        raise HTTPException(status_code=401, detail="Please use Google login for this account")
    
    if not AuthService.verify_password(credentials.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Create session
    token = await AuthService.create_session(str(user["_id"]))
    
    return {
        "token": token,
        "user": AuthService.format_user_response(user)
    }


@router.post("/auth/google", response_model=dict)
async def google_auth(data: GoogleAuthRequest):
    """Authenticate with Google OAuth"""
    # Check if user exists (case-insensitive email matching)
    user = await db.users.find_one({
        "$or": [
            {"email": {"$regex": f"^{re.escape(data.email)}$", "$options": "i"}},
            {"google_id": data.google_id}
        ]
    })
    
    if user:
        # Update google_id if not set
        if not user.get("google_id"):
            await AuthService.update_user_google_id(user["_id"], data.google_id)
    else:
        # Create new user
        username = data.name.replace(" ", "_").lower() if data.name else data.email.split("@")[0]
        # Make username unique
        base_username = username
        counter = 1
        while await db.users.find_one({"username": username}):
            username = f"{base_username}{counter}"
            counter += 1
        
        user = await AuthService.create_user(
            email=data.email,
            username=username,
            google_id=data.google_id
        )
    
    # Create session
    token = await AuthService.create_session(str(user["_id"]))
    
    return {
        "token": token,
        "user": AuthService.format_user_response(user)
    }


@router.get("/auth/me", response_model=dict)
async def get_me(user = Depends(get_current_user)):
    """Get current user profile"""
    return AuthService.format_user_response(user)


@router.get("/auth/google/session-data")
async def get_session_data(session_id: str):
    """Get user data from Emergent Auth session"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"https://emergentintegrations.ai/api/oauth/user/{session_id}"
            )
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Emergent auth returned {response.status_code}: {response.text}")
                raise HTTPException(status_code=500, detail="Failed to verify Google session")
    except httpx.TimeoutException:
        logger.error("Timeout connecting to Emergent auth")
        raise HTTPException(status_code=500, detail="Authentication service timeout")
    except Exception as e:
        logger.error(f"Session verification error: {e}")
        raise HTTPException(status_code=500, detail="Failed to verify Google session")
