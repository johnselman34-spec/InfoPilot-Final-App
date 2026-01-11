"""
InfoPilot Explorer - Main Application
A specialized search engine with protocol-based collation
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio

from config import db, logger, client

# Import routers
from routes.auth import router as auth_router
from routes.categories import router as categories_router
from routes.search import router as search_router
from routes.marketplace import router as marketplace_router
from routes.admin import router as admin_router
from routes.social import router as social_router


# Create FastAPI app
app = FastAPI(
    title="InfoPilot Explorer API",
    description="A specialized search engine with protocol-based result collation and marketplace",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== HEALTH CHECK ====================

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    from datetime import datetime
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


# ==================== INCLUDE ROUTERS ====================

app.include_router(auth_router, prefix="/api")
app.include_router(categories_router, prefix="/api")
app.include_router(search_router, prefix="/api")
app.include_router(marketplace_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(social_router, prefix="/api")


# ==================== DATABASE STARTUP ====================

async def create_indexes_with_retry(max_retries=5, delay=3):
    """Create database indexes with retry logic for Atlas connection"""
    for attempt in range(max_retries):
        try:
            await client.admin.command('ping')
            logger.info(f"MongoDB connection successful (attempt {attempt + 1})")
            
            # Create indexes
            await db.users.create_index("email", unique=True)
            await db.users.create_index("username", unique=True)
            await db.categories.create_index([("user_id", 1), ("name", 1)])
            await db.search_results.create_index([("user_id", 1), ("url", 1)])
            await db.newsletters.create_index([("generated_at", -1)])
            await db.marketplace_protocols.create_index([("category", 1), ("status", 1)])
            await db.marketplace_purchases.create_index([("user_id", 1), ("protocol_id", 1)])
            
            logger.info("Database indexes created successfully")
            return True
        except Exception as e:
            logger.warning(f"MongoDB connection attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(delay)
            else:
                logger.error(f"Failed to connect to MongoDB after {max_retries} attempts")
                return False


@app.on_event("startup")
async def startup_db_client():
    await create_indexes_with_retry()


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()


# ==================== RUN ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
