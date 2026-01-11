"""
InfoPilot Explorer - Configuration Module
Central configuration for the application
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import resend
import logging

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB Configuration
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'infopilot_db')

# Configure MongoDB client with Atlas-compatible settings
client = AsyncIOMotorClient(
    MONGO_URL,
    serverSelectionTimeoutMS=30000,
    connectTimeoutMS=30000,
    socketTimeoutMS=30000,
    retryWrites=True,
    w='majority'
)
db = client[DB_NAME]

# PayPal Configuration - credentials must be set in .env file
PAYPAL_CLIENT_ID = os.environ.get('PAYPAL_CLIENT_ID')
PAYPAL_SECRET = os.environ.get('PAYPAL_SECRET')
PAYPAL_HOSTED_BUTTON_ID = os.environ.get('PAYPAL_HOSTED_BUTTON_ID')
PAYPAL_PAYMENT_LINK = os.environ.get('PAYPAL_PAYMENT_LINK', 'https://py.pl/vdf9TkEwfV1ngxIsu9JzlQ')

# Resend Email Configuration
RESEND_API_KEY = os.environ.get('RESEND_API_KEY')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'onboarding@resend.dev')
if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY

# Emergent LLM Key
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')

# SerpAPI Key
SERPAPI_KEY = os.environ.get('SERPAPI_KEY')

# Protocol Marketplace Settings
MARKETPLACE_PLATFORM_FEE = 0.10  # 10% platform fee, 90% to creators
MARKETPLACE_MIN_PRICE = 0.99
MARKETPLACE_MAX_PRICE = 99.99

# Book Promotion Data
BOOK_PROMO = {
    "title": "Letters to Evelyn",
    "author": "John Selman",
    "genre": "A True Supernatural Thriller Comedy",
    "price": "$2.99",
    "amazon_url": "https://www.amazon.com/Letters-Evelyn-John-Selman-ebook/dp/B0CQZ8R191",
    "reviews_url": "https://readersfavorite.com/book-review/letters-to-evelyn",
    "review_count": 19,
    "review_source": "Readers' Favorite",
    "featured_review": {
        "reviewer": "Divine Zape",
        "source": "Readers' Favorite",
        "quote": "This memoir is a profound and unforgettable literary piece."
    },
    "images": [
        "https://customer-assets.emergentagent.com/job_search-explorer-5/artifacts/rtfq9tzg_Letters%20to%20Evelyn%20advertisement%201.jpg",
        "https://customer-assets.emergentagent.com/job_search-explorer-5/artifacts/c525b6c3_Letters%20to%20Evelyn%20advertisement%202.jpg",
        "https://customer-assets.emergentagent.com/job_search-explorer-5/artifacts/w9somusu_Letters%20to%20Evelyn%20advertisement%203.jpg",
        "https://customer-assets.emergentagent.com/job_search-explorer-5/artifacts/km4oz6iz_Letters%20to%20Evelyn%20advertisement%204.jpg"
    ]
}
