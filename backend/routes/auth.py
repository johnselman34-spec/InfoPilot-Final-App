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
    except Exception:
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
    from bson import ObjectId
    
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
        # Re-fetch to get the latest is_admin and other fields
        user = await db.users.find_one({"_id": user["_id"]})
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
        # Re-fetch to get all fields including _id
        user = await db.users.find_one({"_id": user["_id"]})
    
    # Create session
    token = await AuthService.create_session(str(user["_id"]))
    
    logger.info(f"Google OAuth login for {data.email} - is_admin: {user.get('is_admin', False)}")
    
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
                "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
                headers={"X-Session-ID": session_id}
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



@router.put("/auth/update-email", response_model=dict)
async def update_email(
    request: dict,
    user = Depends(get_current_user)
):
    """Update user email - requires password verification"""
    from bson import ObjectId
    
    new_email = request.get("new_email")
    password = request.get("password")
    
    if not new_email or not password:
        raise HTTPException(status_code=400, detail="Both new_email and password are required")
    
    # Validate new email format
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, new_email):
        raise HTTPException(status_code=400, detail="Invalid email format")
    
    # Check if email already exists (case-insensitive)
    existing = await db.users.find_one({
        "email": {"$regex": f"^{re.escape(new_email)}$", "$options": "i"},
        "_id": {"$ne": user["_id"]}
    })
    if existing:
        raise HTTPException(status_code=400, detail="Email already in use by another account")
    
    # Verify password
    if user.get("password_hash"):
        if not AuthService.verify_password(password, user["password_hash"]):
            raise HTTPException(status_code=400, detail="Incorrect password")
    else:
        # Google OAuth user without password - require them to set one first
        raise HTTPException(status_code=400, detail="Please set a password first before changing email")
    
    # Update email
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"email": new_email.lower(), "updated_at": datetime.utcnow()}}
    )
    
    logger.info(f"User {user['_id']} changed email from {user.get('email')} to {new_email}")
    
    # Fetch updated user
    updated_user = await db.users.find_one({"_id": user["_id"]})
    
    return {
        "success": True,
        "message": "Email updated successfully!",
        "user": AuthService.format_user_response(updated_user)
    }


@router.put("/auth/change-password", response_model=dict)
async def change_password(
    current_password: str = None,
    new_password: str = None,
    user = Depends(get_current_user)
):
    """Change or set password"""
    from bson import ObjectId
    
    if not new_password or len(new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters")
    
    # If user has a password, verify the current one
    if user.get("password_hash"):
        if not current_password:
            raise HTTPException(status_code=400, detail="Current password is required")
        if not AuthService.verify_password(current_password, user["password_hash"]):
            raise HTTPException(status_code=400, detail="Incorrect current password")
    
    # Hash and save new password
    new_hash = AuthService.hash_password(new_password)
    
    await db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"password_hash": new_hash, "updated_at": datetime.utcnow()}}
    )
    
    logger.info(f"User {user['_id']} changed password")
    
    return {
        "success": True,
        "message": "Password updated successfully!"
    }
