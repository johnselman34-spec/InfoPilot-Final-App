# Routers module
from .auth import router as auth_router, require_auth
from .categories import router as categories_router
from .groups import router as groups_router
from .social import router as social_router
from .chat import router as chat_router
from .marketplace import router as marketplace_router
from .easter_eggs import router as easter_eggs_router
from .pages import router as pages_router
from .search import router as search_router
from .stats import router as stats_router
from .paypal import router as paypal_router
from .users import router as users_router

__all__ = [
    'auth_router', 'require_auth',
    'categories_router',
    'groups_router', 
    'social_router',
    'chat_router',
    'marketplace_router',
    'easter_eggs_router',
    'pages_router',
    'search_router',
    'stats_router',
    'paypal_router',
    'users_router'
]
