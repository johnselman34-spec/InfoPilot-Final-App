"""Email notification service using SendGrid"""
import logging
import os

# SendGrid for email notifications
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False

logger = logging.getLogger(__name__)

SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY', '')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'noreply@infopilot-explorer.com')

async def send_notification_email(to_email: str, subject: str, html_content: str):
    """Send email notification using SendGrid"""
    if not SENDGRID_AVAILABLE or not SENDGRID_API_KEY:
        logger.warning("SendGrid not configured - email notification skipped")
        return False
    
    try:
        message = Mail(
            from_email=SENDER_EMAIL,
            to_emails=to_email,
            subject=subject,
            html_content=html_content
        )
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        return response.status_code == 202
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False
