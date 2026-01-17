"""
InfoPilot Explorer - Scheduled Domain Quality Scoring
Automatically runs domain analysis and sends email notifications for critical/warning alerts
"""
import os
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

# Global scheduler instance
domain_scheduler: Optional[AsyncIOScheduler] = None

# Alert level emojis and colors for email
ALERT_STYLES = {
    "critical": {"emoji": "🔴", "color": "#ef4444", "name": "CRITICAL"},
    "warning": {"emoji": "🟡", "color": "#f59e0b", "name": "WARNING"},
    "watch": {"emoji": "🔵", "color": "#3b82f6", "name": "WATCH"}
}

async def run_domain_scoring():
    """Run domain scoring analysis and send notifications if needed"""
    from config import db
    
    logger.info("🔍 Starting scheduled domain scoring analysis...")
    
    try:
        # Get schedule config
        config = await db.domain_scoring_config.find_one({"type": "schedule"})
        if not config or not config.get("enabled"):
            logger.info("Domain scoring scheduler is disabled, skipping...")
            return
        
        # Run the domain scoring analysis
        # Same logic as the manual endpoint
        
        CRITICAL_THRESHOLD = 30
        WARNING_THRESHOLD = 45
        WATCH_THRESHOLD = 55
        
        # Analyze domains with at least 5 results
        domain_analysis_pipeline = [
            {"$match": {"root_domain": {"$exists": True, "$ne": ""}}},
            {"$group": {
                "_id": "$root_domain",
                "avg_score": {"$avg": {"$ifNull": ["$content_quality_score", 50]}},
                "result_count": {"$sum": 1},
                "min_score": {"$min": {"$ifNull": ["$content_quality_score", 50]}},
                "max_score": {"$max": {"$ifNull": ["$content_quality_score", 50]}},
                "latest_result": {"$max": "$created_at"}
            }},
            {"$match": {"result_count": {"$gte": 5}}},
            {"$sort": {"avg_score": 1}}
        ]
        
        all_domains = await db.search_results.aggregate(domain_analysis_pipeline).to_list(1000)
        
        # Get already blocked domains
        blocked = await db.blocked_domains.distinct("domain")
        blocked_set = set(blocked)
        
        alerts_created = 0
        alerts_updated = 0
        new_critical = 0
        new_warning = 0
        new_alerts = []
        
        for domain_data in all_domains:
            domain = domain_data["_id"]
            avg_score = domain_data["avg_score"]
            result_count = domain_data["result_count"]
            
            if domain in blocked_set:
                continue
            
            # Determine alert level
            if avg_score < CRITICAL_THRESHOLD:
                alert_level = "critical"
                alert_message = f"Critical: {domain} has very low quality (avg: {avg_score:.1f})"
            elif avg_score < WARNING_THRESHOLD:
                alert_level = "warning"
                alert_message = f"Warning: {domain} has below-average quality (avg: {avg_score:.1f})"
            elif avg_score < WATCH_THRESHOLD:
                alert_level = "watch"
                alert_message = f"Watch: {domain} quality is declining (avg: {avg_score:.1f})"
            else:
                await db.domain_alerts.delete_one({"domain": domain})
                continue
            
            # Check for existing alert
            existing_alert = await db.domain_alerts.find_one({"domain": domain})
            
            if existing_alert:
                await db.domain_alerts.update_one(
                    {"domain": domain},
                    {"$set": {
                        "alert_level": alert_level,
                        "avg_score": round(avg_score, 1),
                        "result_count": result_count,
                        "min_score": round(domain_data["min_score"], 1),
                        "max_score": round(domain_data["max_score"], 1),
                        "message": alert_message,
                        "latest_result": domain_data.get("latest_result"),
                        "updated_at": datetime.utcnow()
                    }}
                )
                alerts_updated += 1
            else:
                await db.domain_alerts.insert_one({
                    "domain": domain,
                    "alert_level": alert_level,
                    "avg_score": round(avg_score, 1),
                    "result_count": result_count,
                    "min_score": round(domain_data["min_score"], 1),
                    "max_score": round(domain_data["max_score"], 1),
                    "message": alert_message,
                    "latest_result": domain_data.get("latest_result"),
                    "dismissed": False,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                })
                alerts_created += 1
                
                # Track new critical/warning alerts for notifications
                if alert_level == "critical":
                    new_critical += 1
                    new_alerts.append({"domain": domain, "level": "critical", "score": round(avg_score, 1)})
                elif alert_level == "warning":
                    new_warning += 1
                    new_alerts.append({"domain": domain, "level": "warning", "score": round(avg_score, 1)})
        
        # Update last run time
        await db.domain_scoring_config.update_one(
            {"type": "schedule"},
            {"$set": {
                "last_run": datetime.utcnow(),
                "last_run_results": {
                    "alerts_created": alerts_created,
                    "alerts_updated": alerts_updated,
                    "new_critical": new_critical,
                    "new_warning": new_warning
                }
            }},
            upsert=True
        )
        
        logger.info(f"✅ Domain scoring complete: {alerts_created} new alerts, {alerts_updated} updated, {new_critical} critical, {new_warning} warning")
        
        # Send email notification if there are new critical or warning alerts
        if (new_critical > 0 or new_warning > 0) and config.get("email_notifications"):
            await send_alert_notification(config, new_critical, new_warning, new_alerts)
        
    except Exception as e:
        logger.error(f"❌ Domain scoring failed: {e}")
        raise


async def send_alert_notification(config: Dict, new_critical: int, new_warning: int, alerts: List[Dict]):
    """Send email notification about new critical/warning alerts"""
    try:
        import resend
        from config import RESEND_API_KEY, SENDER_EMAIL
        
        if not RESEND_API_KEY:
            logger.warning("RESEND_API_KEY not configured, skipping email notification")
            return
        
        resend.api_key = RESEND_API_KEY
        
        recipients = config.get("notification_emails", ["jjspilot24@gmail.com"])
        if not recipients:
            return
        
        # Build email content
        subject = f"🚨 Domain Quality Alert: {new_critical} Critical, {new_warning} Warning"
        
        alerts_html = ""
        for alert in alerts[:10]:  # Limit to 10 alerts in email
            style = ALERT_STYLES.get(alert["level"], ALERT_STYLES["watch"])
            alerts_html += f'''
                <tr style="border-bottom: 1px solid #333;">
                    <td style="padding: 10px;">{style["emoji"]} {alert["domain"]}</td>
                    <td style="padding: 10px; color: {style["color"]}; font-weight: bold;">{style["name"]}</td>
                    <td style="padding: 10px; text-align: center;">{alert["score"]}</td>
                </tr>
            '''
        
        html_content = f'''
        <div style="font-family: Arial, sans-serif; background-color: #1a0a30; color: #e2e8f0; padding: 30px; border-radius: 12px;">
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #f472b6; margin: 0;">🔔 Domain Quality Alert</h1>
                <p style="color: #a1a1aa;">Automatic Domain Scoring has detected new alerts</p>
            </div>
            
            <div style="display: flex; justify-content: center; gap: 20px; margin-bottom: 30px;">
                <div style="background: rgba(239, 68, 68, 0.2); padding: 20px; border-radius: 10px; text-align: center; min-width: 120px;">
                    <div style="font-size: 2rem; font-weight: bold; color: #ef4444;">{new_critical}</div>
                    <div style="color: #ef4444;">Critical</div>
                </div>
                <div style="background: rgba(245, 158, 11, 0.2); padding: 20px; border-radius: 10px; text-align: center; min-width: 120px;">
                    <div style="font-size: 2rem; font-weight: bold; color: #f59e0b;">{new_warning}</div>
                    <div style="color: #f59e0b;">Warning</div>
                </div>
            </div>
            
            <h3 style="color: #f472b6;">New Alerts:</h3>
            <table style="width: 100%; border-collapse: collapse; background: rgba(30, 20, 50, 0.5); border-radius: 8px;">
                <thead>
                    <tr style="border-bottom: 2px solid #7c3aed;">
                        <th style="padding: 12px; text-align: left; color: #a1a1aa;">Domain</th>
                        <th style="padding: 12px; text-align: left; color: #a1a1aa;">Level</th>
                        <th style="padding: 12px; text-align: center; color: #a1a1aa;">Score</th>
                    </tr>
                </thead>
                <tbody>
                    {alerts_html}
                </tbody>
            </table>
            
            <div style="margin-top: 30px; text-align: center;">
                <a href="https://infopilotexplorer.biz/admin" style="background: linear-gradient(135deg, #7c3aed, #a78bfa); color: white; padding: 12px 30px; border-radius: 8px; text-decoration: none; font-weight: bold;">
                    View in Admin Panel →
                </a>
            </div>
            
            <div style="margin-top: 30px; padding: 15px; background: rgba(16, 185, 129, 0.1); border-radius: 8px; text-align: center;">
                <p style="color: #10b981; margin: 0;">💡 <strong>Tip:</strong> Review these domains and consider blocking consistently low-quality sources to improve your content library.</p>
            </div>
            
            <div style="margin-top: 30px; text-align: center; color: #71717a; font-size: 0.85rem;">
                <p>This is an automated notification from InfoPilot Explorer.</p>
                <p>You can manage notification settings in the Admin Panel → Quality Analytics tab.</p>
            </div>
        </div>
        '''
        
        resend.Emails.send({
            "from": SENDER_EMAIL,
            "to": recipients,
            "subject": subject,
            "html": html_content
        })
        
        logger.info(f"📧 Alert notification sent to {len(recipients)} recipients")
        
    except Exception as e:
        logger.error(f"Failed to send alert notification: {e}")


def start_domain_scoring_scheduler():
    """Start the domain scoring scheduler"""
    global domain_scheduler
    
    if domain_scheduler is not None:
        logger.info("Domain scoring scheduler already running")
        return
    
    domain_scheduler = AsyncIOScheduler()
    
    # Add job to check and run scoring based on config
    # This runs every hour to check if it's time to run based on schedule
    domain_scheduler.add_job(
        check_and_run_scoring,
        CronTrigger(minute=0),  # Check every hour at minute 0
        id="domain_scoring_check",
        replace_existing=True
    )
    
    domain_scheduler.start()
    logger.info("🔍 Domain scoring scheduler started!")


async def check_and_run_scoring():
    """Check if it's time to run scoring based on schedule config"""
    from config import db
    
    try:
        config = await db.domain_scoring_config.find_one({"type": "schedule"})
        
        if not config or not config.get("enabled"):
            return
        
        schedule = config.get("schedule", "daily")
        last_run = config.get("last_run")
        run_hour = config.get("run_hour", 6)  # Default: 6 AM
        
        now = datetime.utcnow()
        current_hour = now.hour
        
        # Check if it's the right hour to run
        if current_hour != run_hour:
            return
        
        # Check if we should run based on schedule
        should_run = False
        
        if schedule == "daily":
            # Run daily if last run was more than 23 hours ago
            if not last_run or (now - last_run).total_seconds() > 23 * 3600:
                should_run = True
        elif schedule == "weekly":
            # Run weekly if last run was more than 6 days ago
            if not last_run or (now - last_run).total_seconds() > 6 * 24 * 3600:
                should_run = True
        elif schedule == "hourly":
            # Run hourly (for testing)
            if not last_run or (now - last_run).total_seconds() > 3500:
                should_run = True
        
        if should_run:
            logger.info(f"⏰ Scheduled domain scoring triggered ({schedule})")
            await run_domain_scoring()
    
    except Exception as e:
        logger.error(f"Error checking domain scoring schedule: {e}")


def stop_domain_scoring_scheduler():
    """Stop the domain scoring scheduler"""
    global domain_scheduler
    
    if domain_scheduler:
        domain_scheduler.shutdown()
        domain_scheduler = None
        logger.info("Domain scoring scheduler stopped")
