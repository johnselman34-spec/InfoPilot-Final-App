"""
InfoPilot Explorer - Main Server
A Worldwide Information Exchange Database
First in Flight with Monetization of Searches! It's a Bear! 🐻

Top Pilot Enterprises, Inc.
"""
from fastapi import FastAPI, WebSocket, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import database
from utils.db import db

# Import route modules
from routes import auth, categories, search, groups, pages, chat, reports, marketplace, revenue, templates, users, misc, email, paypal, stripe, admin

# Import WebSocket handler
from utils.websocket import websocket_handler
from utils.db_optimization import create_indexes


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info("🚀 InfoPilot Explorer API starting...")
    
    # Create comprehensive indexes for better performance
    await create_indexes()
    
    # Legacy indexes (kept for backward compatibility)
    await db.users.create_index("email", unique=True)
    await db.users.create_index("username", unique=True)
    await db.users.create_index("id", unique=True)
    await db.sessions.create_index("token", unique=True)
    await db.sessions.create_index("user_id")
    await db.categories.create_index("user_id")
    await db.categories.create_index("id", unique=True)
    await db.categories.create_index([("is_public", 1), ("price", 1)])
    await db.search_results.create_index("user_id")
    await db.search_results.create_index("category_ids")
    await db.personal_reports.create_index("user_id")
    await db.chat_rooms.create_index([("is_public", 1)])
    await db.chat_messages.create_index("room_id")
    await db.groups.create_index([("is_public", 1)])
    await db.pages.create_index("owner_id")
    await db.purchases.create_index([("seller_id", 1), ("status", 1)])
    
    # Initialize admin settings if not exists
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
    
    # Create admin user if not exists
    admin = await db.users.find_one({"email": "admin@infopilot.com"})
    if not admin:
        from utils.auth import hash_password
        import uuid
        admin_user = {
            "id": str(uuid.uuid4()),
            "email": "admin@infopilot.com",
            "username": "InfoPilotAdmin",
            "hashed_password": hash_password("admin123"),
            "is_admin": True,
            "is_paid": True,
            "laughter_points": 0,
            "easter_eggs_caught": 0,
            "theme_settings": {"mode": "dark", "preset": "cosmic"}
        }
        await db.users.insert_one(admin_user)
        logger.info("Admin user created: admin@infopilot.com")
    
    logger.info("✨ InfoPilot Explorer API started! It's a Bear! 🐻")
    yield
    logger.info("👋 InfoPilot Explorer API shutting down...")


# Create FastAPI app
app = FastAPI(
    title="InfoPilot Explorer API",
    description="Worldwide Information Exchange Database - First in Flight with Monetization of Searches!",
    version="3.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include route modules with /api prefix
app.include_router(auth.router, prefix="/api")
app.include_router(categories.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(groups.router, prefix="/api")
app.include_router(pages.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(marketplace.router, prefix="/api")
app.include_router(revenue.router, prefix="/api")
app.include_router(templates.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(misc.router, prefix="/api")
app.include_router(email.router, prefix="/api/email")
app.include_router(paypal.router, prefix="/api/paypal")
app.include_router(stripe.router, prefix="/api/stripe")


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "InfoPilot Explorer API",
        "version": "3.0.0",
        "tagline": "First in Flight with Monetization of Searches! It's a Bear! 🐻",
        "company": "Top Pilot Enterprises, Inc.",
        "status": "operational"
    }


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "InfoPilot Explorer"}


# WebSocket endpoint for real-time chat
@app.websocket("/api/chat/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(None)):
    """WebSocket endpoint for real-time chat."""
    await websocket_handler(websocket, token)
