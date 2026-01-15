"""
InfoPilot Explorer - Revenue Forecasting Service
AI-powered revenue predictions based on A/B test performance trends
"""
import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


async def get_revenue_data(days: int = 30) -> Dict:
    """
    Get revenue data from A/B tests and protocol sales
    """
    from config import db
    
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Get A/B test events
    ab_events = await db.ab_events.find({
        "timestamp": {"$gte": cutoff}
    }).to_list(10000)
    
    # Get protocol purchases
    purchases = await db.purchases.find({
        "created_at": {"$gte": cutoff}
    }).to_list(1000)
    
    # Calculate daily stats
    daily_stats = {}
    
    for event in ab_events:
        date = event.get("timestamp", datetime.now(timezone.utc)).strftime("%Y-%m-%d")
        if date not in daily_stats:
            daily_stats[date] = {"impressions": 0, "conversions": 0, "revenue": 0}
        
        if event.get("event_type") == "impression":
            daily_stats[date]["impressions"] += 1
        elif event.get("event_type") == "conversion":
            daily_stats[date]["conversions"] += 1
    
    for purchase in purchases:
        date = purchase.get("created_at", datetime.now(timezone.utc)).strftime("%Y-%m-%d")
        if date not in daily_stats:
            daily_stats[date] = {"impressions": 0, "conversions": 0, "revenue": 0}
        daily_stats[date]["revenue"] += purchase.get("amount", 0)
    
    # Calculate totals
    total_impressions = sum(d["impressions"] for d in daily_stats.values())
    total_conversions = sum(d["conversions"] for d in daily_stats.values())
    total_revenue = sum(d["revenue"] for d in daily_stats.values())
    
    # Calculate averages
    num_days = max(len(daily_stats), 1)
    avg_daily_impressions = total_impressions / num_days
    avg_daily_conversions = total_conversions / num_days
    avg_daily_revenue = total_revenue / num_days
    
    conversion_rate = (total_conversions / total_impressions * 100) if total_impressions > 0 else 0
    
    return {
        "period_days": days,
        "daily_stats": daily_stats,
        "totals": {
            "impressions": total_impressions,
            "conversions": total_conversions,
            "revenue": total_revenue,
            "conversion_rate": conversion_rate
        },
        "averages": {
            "daily_impressions": avg_daily_impressions,
            "daily_conversions": avg_daily_conversions,
            "daily_revenue": avg_daily_revenue
        }
    }


async def generate_ai_forecast(revenue_data: Dict, forecast_days: int = 30) -> Dict:
    """
    Generate AI-powered revenue forecast using GPT-5.2
    """
    try:
        from emergentintegrations.llm.chat import chat, Message, ModelType
        
        totals = revenue_data.get("totals", {})
        averages = revenue_data.get("averages", {})
        period = revenue_data.get("period_days", 30)
        
        prompt = f"""You are a witty financial analyst specializing in A/B testing and conversion optimization. Analyze this data and provide a revenue forecast.

HISTORICAL DATA (Last {period} days):
- Total Impressions: {totals.get('impressions', 0):,}
- Total Conversions: {totals.get('conversions', 0):,}
- Conversion Rate: {totals.get('conversion_rate', 0):.2f}%
- Total Revenue: ${totals.get('revenue', 0):.2f}

DAILY AVERAGES:
- Avg Daily Impressions: {averages.get('daily_impressions', 0):.1f}
- Avg Daily Conversions: {averages.get('daily_conversions', 0):.1f}
- Avg Daily Revenue: ${averages.get('daily_revenue', 0):.2f}

TASK: Forecast the next {forecast_days} days. Provide:
1. Projected revenue (conservative, expected, optimistic scenarios)
2. Key factors that could impact the forecast
3. ONE specific, actionable recommendation to increase revenue
4. A funny but insightful closing remark

Format your response as JSON:
{{
    "conservative_revenue": <number>,
    "expected_revenue": <number>,
    "optimistic_revenue": <number>,
    "confidence_level": "<low|medium|high>",
    "key_factors": ["factor1", "factor2", "factor3"],
    "recommendation": "<specific action>",
    "funny_insight": "<witty remark>",
    "weekly_breakdown": [
        {{"week": 1, "projected": <number>}},
        {{"week": 2, "projected": <number>}},
        {{"week": 3, "projected": <number>}},
        {{"week": 4, "projected": <number>}}
    ]
}}"""

        response = await chat(
            api_key=os.environ.get("EMERGENT_API_KEY", ""),
            messages=[Message(role="user", content=prompt)],
            model=ModelType.GPT_5_2
        )
        
        if response and response.content:
            import json
            # Try to parse as JSON
            try:
                # Find JSON in response
                content = response.content
                start = content.find('{')
                end = content.rfind('}') + 1
                if start >= 0 and end > start:
                    forecast = json.loads(content[start:end])
                    forecast["ai_generated"] = True
                    return forecast
            except json.JSONDecodeError:
                pass
        
        return get_fallback_forecast(revenue_data, forecast_days)
        
    except Exception as e:
        logger.error(f"AI forecast generation failed: {e}")
        return get_fallback_forecast(revenue_data, forecast_days)


def get_fallback_forecast(revenue_data: Dict, forecast_days: int = 30) -> Dict:
    """
    Generate fallback forecast based on historical averages
    """
    averages = revenue_data.get("averages", {})
    daily_revenue = averages.get("daily_revenue", 0)
    daily_conversions = averages.get("daily_conversions", 0)
    
    expected = daily_revenue * forecast_days
    conservative = expected * 0.7
    optimistic = expected * 1.5
    
    weekly_revenue = daily_revenue * 7
    
    return {
        "conservative_revenue": round(conservative, 2),
        "expected_revenue": round(expected, 2),
        "optimistic_revenue": round(optimistic, 2),
        "confidence_level": "medium" if daily_revenue > 0 else "low",
        "key_factors": [
            "Historical conversion rate trends",
            "Traffic volume consistency",
            "A/B test optimization opportunities"
        ],
        "recommendation": "Focus on optimizing your top-performing A/B test variants to maximize conversions." if daily_conversions > 0 else "Start A/B testing to gather conversion data for better predictions!",
        "funny_insight": "Remember: Past performance doesn't guarantee future results, but it's better than asking a Magic 8-Ball! 🎱" if daily_revenue > 0 else "Your revenue crystal ball is foggy - more data needed! Time to A/B test like your retirement depends on it! 💰",
        "weekly_breakdown": [
            {"week": i + 1, "projected": round(weekly_revenue * (1 + 0.05 * i), 2)}
            for i in range(4)
        ],
        "ai_generated": False
    }


async def get_full_forecast(days: int = 30, forecast_days: int = 30) -> Dict:
    """
    Get complete revenue forecast with historical data and AI predictions
    """
    # Get historical data
    revenue_data = await get_revenue_data(days)
    
    # Generate AI forecast
    forecast = await generate_ai_forecast(revenue_data, forecast_days)
    
    return {
        "historical_data": revenue_data,
        "forecast": forecast,
        "forecast_period_days": forecast_days,
        "generated_at": datetime.now(timezone.utc).isoformat()
    }
