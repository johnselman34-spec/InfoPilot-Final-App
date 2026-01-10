"""Services package"""
from services.email_service import send_notification_email
from services.websocket_manager import ws_manager, ConnectionManager
from services.protocol_parser import InfoPilot2Parser
