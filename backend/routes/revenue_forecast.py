"""
InfoPilot Explorer - Revenue Forecasting API Routes
AI-powered revenue predictions based on A/B test performance
"""
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
from typing import Optional

from config import db
from routes.auth import get_current_user
from services.revenue_forecast import get_revenue_data, get_full_forecast

router = APIRouter(prefix="/revenue-forecast", tags=["Revenue Forecasting"])


async def require_admin(user = Depends(get_current_user)):
    """Require user to be an admin"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


@router.get("/data")
async def get_historical_data(days: int = 30, user = Depends(require_admin)):
    """Get historical revenue and conversion data"""
    data = await get_revenue_data(days)
    return data


@router.get("/forecast")
async def get_forecast(
    history_days: int = 30, 
    forecast_days: int = 30,
    user = Depends(require_admin)
):
    """
    Get AI-powered revenue forecast
    
    - history_days: Number of days of historical data to analyze
    - forecast_days: Number of days to forecast into the future
    """
    forecast = await get_full_forecast(history_days, forecast_days)
    return forecast


@router.get("/summary")
async def get_revenue_summary(user = Depends(require_admin)):
    """Get quick revenue summary for dashboard"""
    # Get last 7 days
    week_data = await get_revenue_data(7)
    # Get last 30 days  
    month_data = await get_revenue_data(30)
    
    week_avg = week_data["averages"]["daily_revenue"]
    month_avg = month_data["averages"]["daily_revenue"]
    
    # Calculate trend
    trend = "up" if week_avg > month_avg else "down" if week_avg < month_avg else "stable"
    trend_percent = ((week_avg - month_avg) / month_avg * 100) if month_avg > 0 else 0
    
    return {
        "weekly": {
            "revenue": week_data["totals"]["revenue"],
            "conversions": week_data["totals"]["conversions"],
            "conversion_rate": week_data["totals"]["conversion_rate"],
            "avg_daily": week_avg
        },
        "monthly": {
            "revenue": month_data["totals"]["revenue"],
            "conversions": month_data["totals"]["conversions"],
            "conversion_rate": month_data["totals"]["conversion_rate"],
            "avg_daily": month_avg
        },
        "trend": trend,
        "trend_percent": round(trend_percent, 1),
        "projected_monthly": round(week_avg * 30, 2)
    }
