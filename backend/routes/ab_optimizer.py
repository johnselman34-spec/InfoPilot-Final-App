"""
InfoPilot Explorer - A/B Test Auto-Optimizer Routes
API endpoints for managing automatic A/B test optimization
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone

from config import db
from routes.auth import get_current_user, require_admin
from services.ab_optimizer import (
    analyze_test,
    auto_optimize_test,
    run_auto_optimizer,
    get_optimization_history,
    get_ai_optimization_advice
)

router = APIRouter(prefix="/ab-optimizer", tags=["A/B Test Auto-Optimizer"])


class OptimizerConfigRequest(BaseModel):
    enabled: bool = False
    min_confidence: float = 95.0
    min_sample_size: int = 100
    auto_disable_losers: bool = True
    notify_on_optimization: bool = True
    check_frequency_hours: int = 24


class OptimizeRequest(BaseModel):
    test_id: str
    dry_run: bool = True


# ==================== ENDPOINTS ====================

@router.get("/status")
async def get_optimizer_status(user = Depends(require_admin)):
    """Get current optimizer configuration and status"""
    config = await db.ab_optimizer_config.find_one({}) or {}
    
    # Count recent optimizations
    recent_count = await db.ab_optimization_logs.count_documents({
        "timestamp": {"$gte": datetime.now(timezone.utc).replace(day=1)}
    })
    
    return {
        "enabled": config.get("enabled", False),
        "min_confidence": config.get("min_confidence", 95.0),
        "min_sample_size": config.get("min_sample_size", 100),
        "auto_disable_losers": config.get("auto_disable_losers", True),
        "notify_on_optimization": config.get("notify_on_optimization", True),
        "check_frequency_hours": config.get("check_frequency_hours", 24),
        "last_run": config.get("last_run"),
        "optimizations_this_month": recent_count
    }


@router.post("/config")
async def update_optimizer_config(config: OptimizerConfigRequest, user = Depends(require_admin)):
    """Update optimizer configuration"""
    await db.ab_optimizer_config.update_one(
        {},
        {"$set": {
            "enabled": config.enabled,
            "min_confidence": config.min_confidence,
            "min_sample_size": config.min_sample_size,
            "auto_disable_losers": config.auto_disable_losers,
            "notify_on_optimization": config.notify_on_optimization,
            "check_frequency_hours": config.check_frequency_hours,
            "updated_at": datetime.now(timezone.utc),
            "updated_by": user.get("email")
        }},
        upsert=True
    )
    
    return {
        "success": True,
        "message": f"Optimizer {'enabled' if config.enabled else 'disabled'} with {config.min_confidence}% confidence threshold"
    }


@router.get("/analyze/{test_id}")
async def analyze_single_test(test_id: str, days: int = 30, user = Depends(require_admin)):
    """
    Analyze a single A/B test for statistical significance
    Returns detailed stats and recommendations
    """
    analysis = await analyze_test(test_id, days)
    
    if "error" in analysis:
        raise HTTPException(status_code=404, detail=analysis["error"])
    
    # Get AI advice
    ai_advice = await get_ai_optimization_advice(analysis)
    analysis["ai_advice"] = ai_advice
    
    return analysis


@router.get("/analyze-all")
async def analyze_all_tests(days: int = 30, user = Depends(require_admin)):
    """
    Analyze all A/B tests for statistical significance
    Returns overview and recommendations for each test
    """
    tests = await db.ab_tests.find({}).to_list(100)
    
    results = {
        "total_tests": len(tests),
        "tests_with_winners": 0,
        "tests_still_testing": 0,
        "tests_no_data": 0,
        "analyses": []
    }
    
    for test in tests:
        test_id = test.get("test_id")
        if not test_id:
            continue
        
        analysis = await analyze_test(test_id, days)
        
        if analysis.get("status") == "winner_found":
            results["tests_with_winners"] += 1
        elif analysis.get("status") == "testing":
            results["tests_still_testing"] += 1
        else:
            results["tests_no_data"] += 1
        
        results["analyses"].append({
            "test_id": test_id,
            "test_name": analysis.get("test_name", test_id),
            "status": analysis.get("status", "unknown"),
            "best_variant": analysis.get("best_variant"),
            "best_rate": analysis.get("best_rate"),
            "can_optimize": analysis.get("can_optimize", False)
        })
    
    return results


@router.post("/optimize")
async def optimize_single_test(request: OptimizeRequest, user = Depends(require_admin)):
    """
    Run optimizer on a single test
    Use dry_run=true to preview changes without applying them
    """
    result = await auto_optimize_test(request.test_id, dry_run=request.dry_run)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


@router.post("/optimize-all")
async def optimize_all_tests(dry_run: bool = True, user = Depends(require_admin)):
    """
    Run optimizer on all tests
    Use dry_run=true to preview changes without applying them
    """
    result = await run_auto_optimizer(dry_run=dry_run)
    return result


@router.get("/history")
async def get_history(limit: int = 50, user = Depends(require_admin)):
    """Get optimization history"""
    history = await get_optimization_history(limit)
    return {
        "history": history,
        "total": len(history)
    }


@router.post("/enable")
async def enable_optimizer(user = Depends(require_admin)):
    """Quick enable auto-optimizer with default settings"""
    await db.ab_optimizer_config.update_one(
        {},
        {"$set": {
            "enabled": True,
            "updated_at": datetime.now(timezone.utc),
            "updated_by": user.get("email")
        }},
        upsert=True
    )
    return {"success": True, "message": "Auto-optimizer enabled! 🚀"}


@router.post("/disable")
async def disable_optimizer(user = Depends(require_admin)):
    """Quick disable auto-optimizer"""
    await db.ab_optimizer_config.update_one(
        {},
        {"$set": {
            "enabled": False,
            "updated_at": datetime.now(timezone.utc),
            "updated_by": user.get("email")
        }},
        upsert=True
    )
    return {"success": True, "message": "Auto-optimizer disabled"}


@router.post("/run-now")
async def run_optimizer_now(
    background_tasks: BackgroundTasks,
    dry_run: bool = False,
    user = Depends(require_admin)
):
    """
    Manually trigger the optimizer to run now
    """
    # Run in background for large datasets
    result = await run_auto_optimizer(dry_run=dry_run)
    
    # Update last run timestamp
    await db.ab_optimizer_config.update_one(
        {},
        {"$set": {"last_run": datetime.now(timezone.utc)}},
        upsert=True
    )
    
    return result
