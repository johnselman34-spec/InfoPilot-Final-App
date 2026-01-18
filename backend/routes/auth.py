"""
InfoPilot Explorer - Authentication Routes
Register, login, logout, and user profile management
"""
from fastapi import APIRouter, HTTPException, Body, Depends
from typing import Dict
from datetime import datetime, timezone, timedelta
import uuid
import os
import secrets
import resend

from models.schemas import UserCreate, UserLogin, User
from utils.db import db
from utils.auth import hash_password, generate_token, get_current_user, require_user

# Admin setup secret key - read from environment
ADMIN_SETUP_SECRET_KEY = os.environ.get("ADMIN_SETUP_SECRET_KEY", "infopilot_setup_2024_bear")

# Email configuration
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "onboarding@resend.dev")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://search-pilot.preview.emergentagent.com")

# Initialize Resend
if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY

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
    if secret_key != ADMIN_SETUP_SECRET_KEY:
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



@router.post("/forgot-password")
async def forgot_password(email: str = Body(..., embed=True)):
    """Send password reset email."""
    # Find user by email
    user = await db.users.find_one({"email": email})
    
    # Always return success to prevent email enumeration attacks
    if not user:
        return {"message": "If an account exists with this email, a reset link has been sent."}
    
    # Generate secure reset token
    reset_token = secrets.token_urlsafe(32)
    expiry = datetime.now(timezone.utc) + timedelta(hours=1)
    
    # Store reset token in database
    await db.password_resets.delete_many({"user_id": user["id"]})  # Remove old tokens
    await db.password_resets.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "email": email,
        "token": reset_token,
        "expires_at": expiry.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    # Send reset email
    reset_url = f"{FRONTEND_URL}/reset-password?token={reset_token}"
    
    if RESEND_API_KEY:
        try:
            resend.Emails.send({
                "from": SENDER_EMAIL,
                "to": email,
                "subject": "Reset Your InfoPilot Password",
                "html": f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <style>
                        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #1a1a2e; color: #fff; padding: 20px; }}
                        .container {{ max-width: 500px; margin: 0 auto; background: #16213e; border-radius: 12px; padding: 30px; }}
                        .logo {{ text-align: center; font-size: 24px; font-weight: bold; color: #f59e0b; margin-bottom: 20px; }}
                        h1 {{ color: #f59e0b; font-size: 20px; }}
                        p {{ color: #ccc; line-height: 1.6; }}
                        .btn {{ display: inline-block; background: linear-gradient(135deg, #f59e0b, #d97706); color: #000; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: 600; margin: 20px 0; }}
                        .footer {{ margin-top: 30px; font-size: 12px; color: #666; text-align: center; }}
                        .warning {{ background: #422006; border: 1px solid #f59e0b; padding: 10px; border-radius: 6px; font-size: 13px; margin-top: 20px; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="logo">🐻 InfoPilot Explorer</div>
                        <h1>Reset Your Password</h1>
                        <p>We received a request to reset your password. Click the button below to create a new password:</p>
                        <a href="{reset_url}" class="btn">Reset Password</a>
                        <div class="warning">
                            ⚠️ This link expires in 1 hour. If you didn't request this reset, you can safely ignore this email.
                        </div>
                        <div class="footer">
                            © Top Pilot Enterprises, Inc.<br>
                            InfoPilot Explorer - First in Flight with Monetization of Searches!
                        </div>
                    </div>
                </body>
                </html>
                """
            })
        except Exception as e:
            # Log error but don't expose it to user
            print(f"Email send error: {e}")
    
    return {"message": "If an account exists with this email, a reset link has been sent."}


@router.post("/reset-password")
async def reset_password(token: str = Body(...), new_password: str = Body(...)):
    """Reset password using token from email."""
    # Find valid reset token
    reset_record = await db.password_resets.find_one({"token": token})
    
    if not reset_record:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    # Check if token is expired
    expiry = datetime.fromisoformat(reset_record["expires_at"].replace("Z", "+00:00"))
    if datetime.now(timezone.utc) > expiry:
        await db.password_resets.delete_one({"token": token})
        raise HTTPException(status_code=400, detail="Reset token has expired. Please request a new one.")
    
    # Validate new password
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    # Update user's password
    result = await db.users.update_one(
        {"id": reset_record["user_id"]},
        {"$set": {"hashed_password": hash_password(new_password)}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Failed to update password")
    
    # Delete used token
    await db.password_resets.delete_one({"token": token})
    
    # Delete all sessions to force re-login
    await db.sessions.delete_many({"user_id": reset_record["user_id"]})
    
    return {"message": "Password reset successfully! You can now log in with your new password."}


@router.get("/verify-reset-token")
async def verify_reset_token(token: str):
    """Verify if a reset token is valid (for frontend validation)."""
    reset_record = await db.password_resets.find_one({"token": token})
    
    if not reset_record:
        raise HTTPException(status_code=400, detail="Invalid reset token")
    
    expiry = datetime.fromisoformat(reset_record["expires_at"].replace("Z", "+00:00"))
    if datetime.now(timezone.utc) > expiry:
        await db.password_resets.delete_one({"token": token})
        raise HTTPException(status_code=400, detail="Reset token has expired")
    
    return {"valid": True, "email": reset_record["email"]}


