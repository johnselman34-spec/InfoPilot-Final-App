"""Services package"""
from services.email_service import send_notification_email
from services.websocket_manager import ws_manager, ConnectionManager
from services.protocol_parser import InfoPilot2Parser
from services.email_digest import (
    generate_weekly_digest_content, 
    create_digest_html, 
    send_weekly_digest,
    process_weekly_digests
)
