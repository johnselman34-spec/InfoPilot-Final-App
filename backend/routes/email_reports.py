"""
InfoPilot Explorer - Email Reports System
Handles scheduled A/B test reports and email configuration
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from datetime import datetime, timezone, timedelta
from typing import Optional
from bson import ObjectId
from pydantic import BaseModel
import os

from config import db, logger
from routes.auth import get_current_user
from services.email_service import (
    send_email, 
    is_email_configured,
    generate_ab_test_report_html,
    generate_ab_test_report_plain
)

router = APIRouter(prefix="/email-reports", tags=["Email Reports"])


# ==================== MODELS ====================

class EmailReportConfig(BaseModel):
    enabled: bool = True
    frequency: str = "weekly"  # daily, weekly, monthly
    recipients: list = ["jjspilot24@gmail.com"]
    day_of_week: int = 1  # Monday = 1
    hour: int = 9  # 9 AM


class TestEmailRequest(BaseModel):
    recipient: str = "jjspilot24@gmail.com"


# ==================== HELPER FUNCTIONS ====================

async def get_ab_dashboard_data(days: int = 7) -> dict:
    """Fetch A/B testing dashboard data for report"""
    from routes.ab_testing import DEFAULT_TESTS
    
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    # Get all tests
    db_tests = await db.ab_tests.find({}).to_list(50)
    all_tests = db_tests + [t for t in DEFAULT_TESTS if not any(d["name"] == t["name"] for d in db_tests)]
    
    test_summaries = []
    for test in all_tests:
        test_name = test["name"]
        
        # Count total events
        total_events = await db.ab_events.count_documents({
            "test_id": test_name,
            "timestamp": {"$gte": start_date}
        })
        
        # Get top variant
        pipeline = [
            {
                "$match": {
                    "test_id": test_name,
                    "event_type": "conversion",
                    "timestamp": {"$gte": start_date}
                }
            },
            {
                "$group": {
                    "_id": "$variant_id",
                    "conversions": {"$sum": 1}
                }
            },
            {"$sort": {"conversions": -1}},
            {"$limit": 1}
        ]
        
        top_variant = await db.ab_events.aggregate(pipeline).to_list(1)
        
        test_summaries.append({
            "name": test_name,
            "description": test.get("description"),
            "target_element": test.get("target_element"),
            "is_active": test.get("is_active", True),
            "variant_count": len(test.get("variants", [])),
            "total_events": total_events,
            "leading_variant": top_variant[0]["_id"] if top_variant else None
        })
    
    # Overall stats
    total_impressions = await db.ab_events.count_documents({
        "event_type": "impression",
        "timestamp": {"$gte": start_date}
    })
    
    total_conversions = await db.ab_events.count_documents({
        "event_type": "conversion",
        "timestamp": {"$gte": start_date}
    })
    
    return {
        "period_days": days,
        "tests": test_summaries,
        "active_tests": sum(1 for t in test_summaries if t["is_active"]),
        "total_impressions": total_impressions,
        "total_conversions": total_conversions,
        "overall_conversion_rate": round(total_conversions / total_impressions * 100, 2) if total_impressions > 0 else 0,
        "generated_at": datetime.now(timezone.utc).isoformat()
    }


async def send_ab_report_email(recipient: str, days: int = 7) -> dict:
    """Generate and send A/B test report email with EXTREME HUMOR"""
    from services.email_scheduler import generate_hilarious_report_html
    
    # Generate hilarious email content
    subject, html_content = await generate_hilarious_report_html(days)
    
    # Send email
    result = await send_email(
        to_email=recipient,
        subject=subject,
        html_content=html_content
    )
    
    # Log the report
    await db.email_report_logs.insert_one({
        "type": "ab_test_report",
        "recipient": recipient,
        "success": result.get("success", False),
        "error": result.get("error"),
        "period_days": days,
        "sent_at": datetime.now(timezone.utc)
    })
    
    return result


# ==================== ENDPOINTS ====================

@router.get("/status", response_model=dict)
async def get_email_status(user = Depends(get_current_user)):
    """Check if email is configured and get report settings"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get current config
    config = await db.email_report_config.find_one({"type": "ab_test_report"})
    
    return {
        "email_configured": is_email_configured(),
        "gmail_address": os.environ.get("GMAIL_ADDRESS", "")[:3] + "***" if os.environ.get("GMAIL_ADDRESS") else None,
        "reports_enabled": config.get("enabled", False) if config else False,
        "frequency": config.get("frequency", "weekly") if config else "weekly",
        "recipients": config.get("recipients", ["jjspilot24@gmail.com"]) if config else ["jjspilot24@gmail.com"],
        "last_sent": config.get("last_sent") if config else None,
        "setup_instructions": not is_email_configured()
    }


@router.get("/setup-instructions", response_model=dict)
async def get_setup_instructions(user = Depends(get_current_user)):
    """Get instructions for setting up Gmail app password"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return {
        "title": "Gmail App Password Setup",
        "steps": [
            {
                "step": 1,
                "title": "Enable 2-Step Verification",
                "description": "Go to your Google Account settings and enable 2-Step Verification if not already enabled.",
                "url": "https://myaccount.google.com/security"
            },
            {
                "step": 2,
                "title": "Generate App Password",
                "description": "Go to App Passwords page and create a new app password for 'Mail' on 'Other (Custom name)'.",
                "url": "https://myaccount.google.com/apppasswords"
            },
            {
                "step": 3,
                "title": "Copy the 16-character Password",
                "description": "Google will show you a 16-character password. Copy it (you won't be able to see it again)."
            },
            {
                "step": 4,
                "title": "Add to Environment Variables",
                "description": "Add these to your backend/.env file:",
                "code": "GMAIL_ADDRESS=jjspilot24@gmail.com\nGMAIL_APP_PASSWORD=your-16-char-password"
            },
            {
                "step": 5,
                "title": "Restart Backend",
                "description": "Restart the backend service to load the new environment variables."
            }
        ],
        "notes": [
            "App passwords are more secure than using your main password",
            "You can revoke the app password anytime from your Google Account",
            "The app password is only for InfoPilot email reports"
        ]
    }


@router.post("/config", response_model=dict)
async def update_report_config(
    config: EmailReportConfig,
    user = Depends(get_current_user)
):
    """Update email report configuration"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    await db.email_report_config.update_one(
        {"type": "ab_test_report"},
        {
            "$set": {
                "enabled": config.enabled,
                "frequency": config.frequency,
                "recipients": config.recipients,
                "day_of_week": config.day_of_week,
                "hour": config.hour,
                "updated_at": datetime.now(timezone.utc),
                "updated_by": str(user["_id"])
            }
        },
        upsert=True
    )
    
    return {
        "success": True,
        "message": "Report configuration updated",
        "config": config.dict()
    }


@router.post("/send-test", response_model=dict)
async def send_test_report(
    request: TestEmailRequest,
    background_tasks: BackgroundTasks,
    user = Depends(get_current_user)
):
    """Send a test A/B report email"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    if not is_email_configured():
        return {
            "success": False,
            "error": "Email not configured. Please set up Gmail app password first.",
            "setup_required": True
        }
    
    # Send in background
    result = await send_ab_report_email(request.recipient, days=7)
    
    return result


@router.post("/send-now", response_model=dict)
async def send_report_now(
    user = Depends(get_current_user)
):
    """Manually trigger sending the A/B report to all configured recipients"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    if not is_email_configured():
        return {
            "success": False,
            "error": "Email not configured",
            "setup_required": True
        }
    
    # Get config
    config = await db.email_report_config.find_one({"type": "ab_test_report"})
    recipients = config.get("recipients", ["jjspilot24@gmail.com"]) if config else ["jjspilot24@gmail.com"]
    
    results = []
    for recipient in recipients:
        result = await send_ab_report_email(recipient, days=7)
        results.append({"recipient": recipient, **result})
    
    # Update last sent
    await db.email_report_config.update_one(
        {"type": "ab_test_report"},
        {"$set": {"last_sent": datetime.now(timezone.utc)}},
        upsert=True
    )
    
    success_count = sum(1 for r in results if r.get("success"))
    
    return {
        "success": success_count > 0,
        "sent_count": success_count,
        "total_recipients": len(recipients),
        "results": results
    }


@router.get("/preview", response_model=dict)
async def preview_report(
    days: int = 7,
    user = Depends(get_current_user)
):
    """Preview the A/B test report content"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    report_data = await get_ab_dashboard_data(days)
    html_content = generate_ab_test_report_html(report_data)
    
    return {
        "report_data": report_data,
        "html_preview": html_content,
        "subject": f"🧪 A/B Test Weekly Report - InfoPilot Explorer ({datetime.now().strftime('%b %d, %Y')})"
    }


@router.get("/history", response_model=dict)
async def get_report_history(
    page: int = 1,
    limit: int = 20,
    user = Depends(get_current_user)
):
    """Get history of sent reports"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    skip = (page - 1) * limit
    total = await db.email_report_logs.count_documents({"type": "ab_test_report"})
    
    logs = await db.email_report_logs.find(
        {"type": "ab_test_report"}
    ).sort("sent_at", -1).skip(skip).limit(limit).to_list(limit)
    
    return {
        "logs": [
            {
                "id": str(log["_id"]),
                "recipient": log["recipient"],
                "success": log["success"],
                "error": log.get("error"),
                "period_days": log.get("period_days"),
                "sent_at": log["sent_at"].isoformat()
            }
            for log in logs
        ],
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit
    }
