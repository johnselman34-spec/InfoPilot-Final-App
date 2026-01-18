"""
InfoPilot Explorer - Service Monitoring
Background health checks and email alerts for service downtime
"""
import os
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Track service states
_service_states: Dict[str, Dict] = {}
_alert_cooldowns: Dict[str, datetime] = {}
ALERT_COOLDOWN_MINUTES = 15  # Don't send duplicate alerts within this window


async def check_service_health() -> Dict:
    """Check health of all services and return status."""
    from utils.db import db
    
    services = {}
    
    # Check MongoDB
    try:
        await db.users.find_one({})
        services["database"] = {"status": "healthy", "message": "Connected"}
    except Exception as e:
        services["database"] = {"status": "down", "message": str(e)}
    
    # Check Elasticsearch
    try:
        from utils.elasticsearch_client import get_elasticsearch_client
        client = get_elasticsearch_client()
        if client and client.ping():
            services["elasticsearch"] = {"status": "healthy", "message": "Connected"}
        else:
            services["elasticsearch"] = {"status": "down", "message": "Not connected"}
    except Exception as e:
        services["elasticsearch"] = {"status": "down", "message": str(e)}
    
    # Check Brave Search API (simple key check)
    brave_key = os.environ.get("BRAVE_SEARCH_API_KEY", "")
    if brave_key:
        services["brave_search"] = {"status": "healthy", "message": "API key configured"}
    else:
        services["brave_search"] = {"status": "warning", "message": "API key not set"}
    
    # Check Stripe
    stripe_key = os.environ.get("STRIPE_API_KEY", "")
    if stripe_key:
        services["stripe"] = {"status": "healthy", "message": "API key configured"}
    else:
        services["stripe"] = {"status": "warning", "message": "API key not set"}
    
    # Check Resend Email
    resend_key = os.environ.get("RESEND_API_KEY", "")
    if resend_key:
        services["email"] = {"status": "healthy", "message": "API key configured"}
    else:
        services["email"] = {"status": "warning", "message": "API key not set"}
    
    return services


async def send_service_alert(service_name: str, status: str, message: str, admin_email: str) -> bool:
    """Send email alert about service status change."""
    global _alert_cooldowns
    
    # Check cooldown
    cooldown_key = f"{service_name}_{status}"
    now = datetime.now(timezone.utc)
    
    if cooldown_key in _alert_cooldowns:
        time_since_last = (now - _alert_cooldowns[cooldown_key]).total_seconds() / 60
        if time_since_last < ALERT_COOLDOWN_MINUTES:
            logger.debug(f"Alert for {service_name} is in cooldown ({time_since_last:.1f} min)")
            return False
    
    try:
        import resend
        resend.api_key = os.environ.get("RESEND_API_KEY")
        
        if not resend.api_key:
            logger.warning("Cannot send alert - Resend API key not configured")
            return False
        
        subject = f"🚨 InfoPilot Alert: {service_name} is {status.upper()}"
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: {'#ef4444' if status == 'down' else '#f59e0b'};">
                Service Alert: {service_name}
            </h2>
            <p><strong>Status:</strong> {status.upper()}</p>
            <p><strong>Message:</strong> {message}</p>
            <p><strong>Time:</strong> {now.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            <hr>
            <p style="color: #666; font-size: 12px;">
                This is an automated alert from InfoPilot Explorer.
                <br>Top Pilot Enterprises, Inc.
            </p>
        </body>
        </html>
        """
        
        resend.Emails.send({
            "from": os.environ.get("SENDER_EMAIL", "onboarding@resend.dev"),
            "to": admin_email,
            "subject": subject,
            "html": html_content
        })
        
        _alert_cooldowns[cooldown_key] = now
        logger.info(f"Service alert sent for {service_name}: {status}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send service alert: {e}")
        return False


async def monitor_services_once(admin_email: Optional[str] = None) -> Dict:
    """Run a single health check and send alerts if needed."""
    global _service_states
    
    current_health = await check_service_health()
    alerts_sent = []
    
    for service_name, current_status in current_health.items():
        previous_status = _service_states.get(service_name, {}).get("status")
        
        # Detect status changes
        if previous_status and previous_status != current_status["status"]:
            if current_status["status"] == "down":
                # Service went down
                if admin_email:
                    sent = await send_service_alert(
                        service_name, 
                        "down", 
                        current_status["message"],
                        admin_email
                    )
                    if sent:
                        alerts_sent.append(f"{service_name} DOWN")
            elif previous_status == "down" and current_status["status"] == "healthy":
                # Service recovered
                if admin_email:
                    sent = await send_service_alert(
                        service_name,
                        "recovered",
                        "Service is back online",
                        admin_email
                    )
                    if sent:
                        alerts_sent.append(f"{service_name} RECOVERED")
        
        # Update state
        _service_states[service_name] = current_status
    
    return {
        "services": current_health,
        "alerts_sent": alerts_sent,
        "checked_at": datetime.now(timezone.utc).isoformat()
    }


async def get_maintenance_mode() -> Dict:
    """Get current maintenance mode status."""
    from utils.db import db
    
    settings = await db.admin_settings.find_one({"id": "admin_settings"})
    if not settings:
        return {"enabled": False, "message": ""}
    
    return {
        "enabled": settings.get("maintenance_mode", False),
        "message": settings.get("maintenance_message", "We're performing scheduled maintenance. Please check back soon!"),
        "estimated_end": settings.get("maintenance_end_time")
    }


async def set_maintenance_mode(enabled: bool, message: str = None, end_time: str = None) -> Dict:
    """Set maintenance mode status."""
    from utils.db import db
    
    update_data = {"maintenance_mode": enabled}
    if message:
        update_data["maintenance_message"] = message
    if end_time:
        update_data["maintenance_end_time"] = end_time
    elif not enabled:
        update_data["maintenance_end_time"] = None
    
    await db.admin_settings.update_one(
        {"id": "admin_settings"},
        {"$set": update_data},
        upsert=True
    )
    
    return await get_maintenance_mode()
