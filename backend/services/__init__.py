"""
InfoPilot Explorer - Services Module
"""
from .auth_service import AuthService
from .search_service import WebSearchService
from .protocol_service import ProtocolParser
from .email_service import (
    send_email, 
    is_email_configured, 
    generate_ab_test_report_html, 
    generate_ab_test_report_plain,
    EmailService
)
