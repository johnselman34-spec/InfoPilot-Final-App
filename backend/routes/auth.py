"""Authentication routes"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone, timedelta
import uuid
import bcrypt
import jwt
import logging
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from utils.database import db
from utils.config import (
    JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRATION_HOURS,
    GOOGLE_CLIENT_IDS
)
from models.schemas import (
    UserCreate, UserLogin, GoogleAuthRequest, 
    UserResponse, TokenResponse, DEFAULT_BLOCKED_WORDS
)

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = logging.getLogger(__name__)

# ============================================
# HELPER FUNCTIONS
# ============================================

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def create_token(user_id: str) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_blocked_words():
    """Get blocked words from admin settings"""
    settings = await db.admin_settings.find_one({"id": "admin_settings"})
    if settings:
        return settings.get("blocked_words", DEFAULT_BLOCKED_WORDS)
    return DEFAULT_BLOCKED_WORDS

def contains_blocked_words(text: str, blocked_words):
    """Check if text contains any blocked words as WHOLE WORDS only."""
    import re
    text_lower = text.lower()
    found = []
    for word in blocked_words:
        pattern = r'\b' + re.escape(word.lower()) + r'\b'
        if re.search(pattern, text_lower):
            found.append(word)
    return len(found) > 0, found

# ============================================
# AUTH ROUTES
# ============================================

@router.post("/register", response_model=TokenResponse)
async def register(data: UserCreate):
    blocked_words = await get_blocked_words()
    has_blocked, found = contains_blocked_words(data.username, blocked_words)
    if has_blocked:
        raise HTTPException(status_code=400, detail=f"Username contains blocked words: {found}")
    
    if await db.users.find_one({"email": data.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    if await db.users.find_one({"username": data.username}):
        raise HTTPException(status_code=400, detail="Username already taken")
    
    # Find the admin user to add as first friend
    admin_user = await db.users.find_one({"is_admin": True})
    admin_id = admin_user["id"] if admin_user else None
    
    user_id = str(uuid.uuid4())
    user = {
        "id": user_id,
        "username": data.username,
        "email": data.email,
        "password_hash": hash_password(data.password),
        "is_admin": False,
        "is_paid": False,
        "profile_photo": None,
        "auth_provider": "email",
        "friends": [admin_id] if admin_id else [],
        "friend_count": 1 if admin_id else 0,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(user)
    
    # Add the new user to admin's friends list
    if admin_id:
        await db.users.update_one(
            {"id": admin_id},
            {"$addToSet": {"friends": user_id}, "$inc": {"friend_count": 1}}
        )
        
        # Create friendship record
        friendship = {
            "id": str(uuid.uuid4()),
            "user_id": admin_id,
            "friend_id": user_id,
            "status": "accepted",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.friendships.insert_one(friendship)
        
        logger.info(f"New user {data.username} added with admin as first friend")
    
    token = create_token(user_id)
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user_id,
            username=data.username,
            email=data.email,
            is_admin=False,
            is_paid=False,
            auth_provider="email",
            created_at=datetime.fromisoformat(user["created_at"])
        )
    )

@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin):
    user = await db.users.find_one({"email": data.email})
    if not user or not verify_password(data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user["id"])
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user["id"],
            username=user["username"],
            email=user["email"],
            is_admin=user.get("is_admin", False),
            is_paid=user.get("is_paid", False),
            profile_photo=user.get("profile_photo"),
            auth_provider=user.get("auth_provider", "email"),
            created_at=datetime.fromisoformat(user["created_at"]) if isinstance(user["created_at"], str) else user["created_at"]
        )
    )

@router.post("/google", response_model=TokenResponse)
async def google_auth(data: GoogleAuthRequest):
    """Google OAuth Authentication - Verifies Google ID tokens"""
    try:
        # Verify the Google ID token
        idinfo = None
        verification_error = None
        
        # Try to verify against all configured client IDs
        for client_id in GOOGLE_CLIENT_IDS:
            try:
                idinfo = id_token.verify_oauth2_token(
                    data.credential,
                    google_requests.Request(),
                    client_id
                )
                break  # Successfully verified
            except ValueError as e:
                verification_error = str(e)
                continue
        
        if idinfo is None:
            logger.warning(f"Google token verification failed: {verification_error}")
            raise HTTPException(status_code=401, detail=f"Invalid Google token: {verification_error}")
        
        # Token is valid - extract user info
        google_email = idinfo.get('email')
        google_name = idinfo.get('name', 'Pilot')
        google_picture = idinfo.get('picture')
        google_sub = idinfo.get('sub')  # Google's unique user ID
        
        if not google_email:
            raise HTTPException(status_code=400, detail="Email not provided by Google")
        
        # Check if email is verified
        if not idinfo.get('email_verified', False):
            raise HTTPException(status_code=400, detail="Google email not verified")
        
        # Check if user exists by email or Google ID
        user = await db.users.find_one({
            "$or": [
                {"email": google_email},
                {"google_id": google_sub}
            ]
        })
        
        if not user:
            # Create new user
            user_id = str(uuid.uuid4())
            username = google_name.replace(' ', '_')[:20] if google_name else f"pilot_{uuid.uuid4().hex[:6]}"
            
            # Ensure unique username
            existing_username = await db.users.find_one({"username": username})
            if existing_username:
                username = f"{username}_{uuid.uuid4().hex[:4]}"
            
            user = {
                "id": user_id,
                "username": username,
                "email": google_email,
                "google_id": google_sub,
                "password_hash": "",  # No password for OAuth users
                "is_admin": False,
                "is_paid": False,
                "profile_photo": google_picture,
                "auth_provider": "google",
                "friends": [],
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.users.insert_one(user)
            logger.info(f"New Google user registered: {google_email}")
        else:
            # Update existing user's Google info if needed
            update_data = {}
            if not user.get("google_id"):
                update_data["google_id"] = google_sub
            if google_picture and not user.get("profile_photo"):
                update_data["profile_photo"] = google_picture
            if user.get("auth_provider") != "google":
                update_data["auth_provider"] = "google"
            
            if update_data:
                await db.users.update_one({"id": user["id"]}, {"$set": update_data})
                user.update(update_data)
        
        token = create_token(user["id"])
        return TokenResponse(
            access_token=token,
            user=UserResponse(
                id=user["id"],
                username=user["username"],
                email=user["email"],
                is_admin=user.get("is_admin", False),
                is_paid=user.get("is_paid", False),
                profile_photo=user.get("profile_photo"),
                auth_provider="google",
                created_at=datetime.fromisoformat(user["created_at"]) if isinstance(user["created_at"], str) else user["created_at"]
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google auth error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Google authentication failed: {str(e)}")
