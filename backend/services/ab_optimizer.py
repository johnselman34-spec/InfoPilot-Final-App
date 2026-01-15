"""
InfoPilot Explorer - A/B Test Auto-Optimizer
Automatically disables losing variants when statistical significance is reached.
Maximizes revenue while you sleep! 🚀💤💰
"""
import os
import math
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class VariantStats:
    """Statistics for a single variant"""
    variant_id: str
    impressions: int
    conversions: int
    conversion_rate: float
    
    @classmethod
    def from_events(cls, variant_id: str, events: List[Dict]) -> 'VariantStats':
        impressions = len([e for e in events if e.get("event_type") == "impression"])
        conversions = len([e for e in events if e.get("event_type") == "conversion"])
        rate = (conversions / impressions * 100) if impressions > 0 else 0
        return cls(variant_id, impressions, conversions, rate)


@dataclass 
class SignificanceResult:
    """Result of statistical significance test"""
    is_significant: bool
    confidence: float
    z_score: float
    winner_id: str
    loser_id: str
    lift: float  # Percentage improvement of winner over loser
    recommendation: str


def calculate_z_score(rate1: float, n1: int, rate2: float, n2: int) -> float:
    """
    Calculate z-score for two-proportion z-test
    Used to determine if the difference between two conversion rates is statistically significant
    """
    if n1 == 0 or n2 == 0:
        return 0
    
    # Convert rates from percentage to proportion
    p1 = rate1 / 100
    p2 = rate2 / 100
    
    # Pooled proportion
    p_pool = (p1 * n1 + p2 * n2) / (n1 + n2)
    
    # Standard error
    se = math.sqrt(p_pool * (1 - p_pool) * (1/n1 + 1/n2))
    
    if se == 0:
        return 0
    
    # Z-score
    z = (p1 - p2) / se
    return z


def z_score_to_confidence(z: float) -> float:
    """
    Convert z-score to confidence level (one-tailed)
    Uses approximation of the cumulative normal distribution
    """
    # Approximation of the CDF of standard normal distribution
    z = abs(z)
    
    # Constants for approximation
    a1 = 0.254829592
    a2 = -0.284496736
    a3 = 1.421413741
    a4 = -1.453152027
    a5 = 1.061405429
    p = 0.3275911
    
    t = 1.0 / (1.0 + p * z)
    y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * math.exp(-z * z / 2)
    
    return y * 100  # Return as percentage


def test_significance(
    variant_a: VariantStats, 
    variant_b: VariantStats,
    min_sample_size: int = 100,
    confidence_threshold: float = 95.0
) -> SignificanceResult:
    """
    Test if the difference between two variants is statistically significant
    """
    # Check minimum sample size
    if variant_a.impressions < min_sample_size or variant_b.impressions < min_sample_size:
        return SignificanceResult(
            is_significant=False,
            confidence=0,
            z_score=0,
            winner_id="",
            loser_id="",
            lift=0,
            recommendation=f"Need more data. Minimum {min_sample_size} impressions per variant required. Current: A={variant_a.impressions}, B={variant_b.impressions}"
        )
    
    # Calculate z-score
    z = calculate_z_score(
        variant_a.conversion_rate, variant_a.impressions,
        variant_b.conversion_rate, variant_b.impressions
    )
    
    confidence = z_score_to_confidence(z)
    
    # Determine winner and loser
    if variant_a.conversion_rate > variant_b.conversion_rate:
        winner = variant_a
        loser = variant_b
    else:
        winner = variant_b
        loser = variant_a
        z = -z  # Flip for correct direction
    
    # Calculate lift
    lift = ((winner.conversion_rate - loser.conversion_rate) / loser.conversion_rate * 100) if loser.conversion_rate > 0 else 0
    
    is_significant = confidence >= confidence_threshold
    
    if is_significant:
        recommendation = f"🏆 Winner found! '{winner.variant_id}' beats '{loser.variant_id}' by {lift:.1f}% with {confidence:.1f}% confidence. Safe to disable loser!"
    elif confidence >= 80:
        recommendation = f"📈 Promising! '{winner.variant_id}' is ahead by {lift:.1f}% with {confidence:.1f}% confidence. Need more data for certainty."
    else:
        recommendation = f"🔬 Too early to call. Difference is {lift:.1f}% but only {confidence:.1f}% confidence. Keep testing!"
    
    return SignificanceResult(
        is_significant=is_significant,
        confidence=confidence,
        z_score=z,
        winner_id=winner.variant_id,
        loser_id=loser.variant_id,
        lift=lift,
        recommendation=recommendation
    )


async def analyze_test(test_id: str, days: int = 30) -> Dict:
    """
    Analyze a single A/B test for statistical significance
    """
    from config import db
    
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Get test details
    test = await db.ab_tests.find_one({"test_id": test_id})
    if not test:
        return {"error": f"Test '{test_id}' not found"}
    
    # Get events
    events = await db.ab_events.find({
        "test_id": test_id,
        "timestamp": {"$gte": cutoff}
    }).to_list(10000)
    
    if not events:
        return {
            "test_id": test_id,
            "test_name": test.get("name", test_id),
            "status": "no_data",
            "message": "No events recorded for this test"
        }
    
    # Calculate stats per variant
    variants = test.get("variants", [])
    variant_stats = []
    
    for v in variants:
        v_id = v.get("variant_id", "")
        v_events = [e for e in events if e.get("variant_id") == v_id]
        stats = VariantStats.from_events(v_id, v_events)
        variant_stats.append(stats)
    
    if len(variant_stats) < 2:
        return {
            "test_id": test_id,
            "test_name": test.get("name", test_id),
            "status": "insufficient_variants",
            "message": "Need at least 2 variants for comparison"
        }
    
    # Sort by conversion rate (best first)
    variant_stats.sort(key=lambda x: x.conversion_rate, reverse=True)
    
    # Compare best variant against others
    best = variant_stats[0]
    comparisons = []
    
    for other in variant_stats[1:]:
        result = test_significance(best, other)
        comparisons.append({
            "variant_a": best.variant_id,
            "variant_a_rate": best.conversion_rate,
            "variant_a_impressions": best.impressions,
            "variant_b": other.variant_id,
            "variant_b_rate": other.conversion_rate,
            "variant_b_impressions": other.impressions,
            "is_significant": result.is_significant,
            "confidence": result.confidence,
            "lift": result.lift,
            "recommendation": result.recommendation
        })
    
    # Overall status
    any_significant = any(c["is_significant"] for c in comparisons)
    
    return {
        "test_id": test_id,
        "test_name": test.get("name", test_id),
        "status": "winner_found" if any_significant else "testing",
        "best_variant": best.variant_id,
        "best_rate": best.conversion_rate,
        "variants": [
            {
                "id": vs.variant_id,
                "impressions": vs.impressions,
                "conversions": vs.conversions,
                "rate": vs.conversion_rate
            }
            for vs in variant_stats
        ],
        "comparisons": comparisons,
        "can_optimize": any_significant,
        "analyzed_at": datetime.now(timezone.utc).isoformat()
    }


async def get_ai_optimization_advice(analysis: Dict) -> str:
    """
    Get AI-powered advice for A/B test optimization
    """
    try:
        from emergentintegrations.llm.chat import chat, Message, ModelType
        
        # Build context
        test_name = analysis.get("test_name", "Unknown")
        best_variant = analysis.get("best_variant", "Unknown")
        best_rate = analysis.get("best_rate", 0)
        comparisons = analysis.get("comparisons", [])
        
        comparison_text = "\n".join([
            f"- {c['variant_a']} ({c['variant_a_rate']:.2f}%) vs {c['variant_b']} ({c['variant_b_rate']:.2f}%): {c['confidence']:.1f}% confidence, {c['lift']:.1f}% lift"
            for c in comparisons
        ])
        
        prompt = f"""You are a witty A/B testing optimization expert. Analyze this data and give ONE specific, actionable recommendation in 2-3 sentences. Be helpful AND funny.

TEST: {test_name}
BEST PERFORMER: {best_variant} with {best_rate:.2f}% conversion rate

COMPARISONS:
{comparison_text}

Consider:
1. Statistical significance (95%+ = safe to optimize)
2. Sample size adequacy
3. Potential revenue impact
4. Risk of premature optimization

Give your recommendation with a relevant emoji:"""

        response = await chat(
            api_key=os.environ.get("EMERGENT_API_KEY", ""),
            messages=[Message(role="user", content=prompt)],
            model=ModelType.GPT_5_2
        )
        
        if response and response.content:
            return response.content
        return get_fallback_advice(analysis)
        
    except Exception as e:
        logger.error(f"AI advice generation failed: {e}")
        return get_fallback_advice(analysis)


def get_fallback_advice(analysis: Dict) -> str:
    """Fallback advice when AI is unavailable"""
    if analysis.get("can_optimize"):
        return f"🎯 Winner detected! '{analysis.get('best_variant')}' is statistically better. Consider disabling underperformers to maximize conversions. Don't let bad variants steal your revenue!"
    
    best_rate = analysis.get("best_rate", 0)
    if best_rate > 5:
        return f"📈 '{analysis.get('best_variant')}' is leading with {best_rate:.1f}% conversion. Keep collecting data - you're close to statistical significance!"
    
    return "🔬 Still in the testing phase. Keep the experiment running to gather more data. Rome wasn't A/B tested in a day!"


async def auto_optimize_test(test_id: str, dry_run: bool = True) -> Dict:
    """
    Automatically optimize a test by disabling losing variants
    
    Args:
        test_id: The test to optimize
        dry_run: If True, only simulate optimization without making changes
    """
    from config import db
    
    # Analyze test first
    analysis = await analyze_test(test_id)
    
    if "error" in analysis:
        return analysis
    
    if not analysis.get("can_optimize"):
        return {
            "test_id": test_id,
            "optimized": False,
            "reason": "No statistically significant winner yet",
            "analysis": analysis
        }
    
    # Find variants to disable
    variants_to_disable = []
    for comp in analysis.get("comparisons", []):
        if comp.get("is_significant") and comp.get("lift") > 0:
            variants_to_disable.append(comp["variant_b"])
    
    if not variants_to_disable:
        return {
            "test_id": test_id,
            "optimized": False,
            "reason": "No variants to disable",
            "analysis": analysis
        }
    
    # Get AI advice
    ai_advice = await get_ai_optimization_advice(analysis)
    
    result = {
        "test_id": test_id,
        "test_name": analysis.get("test_name"),
        "winner": analysis.get("best_variant"),
        "losers_to_disable": variants_to_disable,
        "ai_advice": ai_advice,
        "dry_run": dry_run,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    if dry_run:
        result["optimized"] = False
        result["reason"] = "Dry run - no changes made"
    else:
        # Actually disable the losing variants
        test = await db.ab_tests.find_one({"test_id": test_id})
        if test:
            updated_variants = []
            for v in test.get("variants", []):
                v_copy = v.copy()
                if v.get("variant_id") in variants_to_disable:
                    v_copy["disabled"] = True
                    v_copy["disabled_at"] = datetime.now(timezone.utc)
                    v_copy["disabled_reason"] = "auto_optimization"
                updated_variants.append(v_copy)
            
            await db.ab_tests.update_one(
                {"test_id": test_id},
                {"$set": {"variants": updated_variants}}
            )
            
            # Log the optimization
            await db.ab_optimization_logs.insert_one({
                "test_id": test_id,
                "test_name": analysis.get("test_name"),
                "winner": analysis.get("best_variant"),
                "disabled_variants": variants_to_disable,
                "ai_advice": ai_advice,
                "analysis_snapshot": analysis,
                "timestamp": datetime.now(timezone.utc)
            })
            
            result["optimized"] = True
            result["reason"] = f"Disabled {len(variants_to_disable)} underperforming variant(s)"
    
    return result


async def run_auto_optimizer(dry_run: bool = True, min_confidence: float = 95.0) -> Dict:
    """
    Run auto-optimizer on all active tests
    """
    from config import db
    
    # Get optimizer config
    config = await db.ab_optimizer_config.find_one({}) or {}
    
    if not config.get("enabled", False) and not dry_run:
        return {
            "success": False,
            "reason": "Auto-optimizer is disabled",
            "tests_checked": 0
        }
    
    # Get all tests
    tests = await db.ab_tests.find({}).to_list(100)
    
    results = {
        "success": True,
        "dry_run": dry_run,
        "tests_checked": len(tests),
        "tests_optimized": 0,
        "optimizations": [],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    for test in tests:
        test_id = test.get("test_id")
        if not test_id:
            continue
        
        optimization = await auto_optimize_test(test_id, dry_run=dry_run)
        
        if optimization.get("optimized"):
            results["tests_optimized"] += 1
        
        results["optimizations"].append({
            "test_id": test_id,
            "test_name": test.get("name", test_id),
            "optimized": optimization.get("optimized", False),
            "reason": optimization.get("reason", ""),
            "winner": optimization.get("winner"),
            "disabled": optimization.get("losers_to_disable", [])
        })
    
    return results


async def get_optimization_history(limit: int = 50) -> List[Dict]:
    """Get recent optimization history"""
    from config import db
    
    logs = await db.ab_optimization_logs.find({}).sort("timestamp", -1).limit(limit).to_list(limit)
    
    return [
        {
            "id": str(log.get("_id")),
            "test_id": log.get("test_id"),
            "test_name": log.get("test_name"),
            "winner": log.get("winner"),
            "disabled_variants": log.get("disabled_variants", []),
            "ai_advice": log.get("ai_advice"),
            "timestamp": log.get("timestamp")
        }
        for log in logs
    ]


# ============== SCHEDULER INTEGRATION ==============

_optimizer_scheduler = None

def start_optimizer_scheduler():
    """Start the A/B optimizer background scheduler"""
    global _optimizer_scheduler
    
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.interval import IntervalTrigger
        import asyncio
        
        _optimizer_scheduler = BackgroundScheduler()
        
        def run_optimizer_job():
            """Background job to run the optimizer"""
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(run_scheduled_optimization())
                logger.info(f"🤖 A/B Optimizer ran: {result.get('tests_optimized', 0)} tests optimized")
            except Exception as e:
                logger.error(f"A/B Optimizer job failed: {e}")
            finally:
                loop.close()
        
        # Run every 6 hours (configurable via db settings)
        _optimizer_scheduler.add_job(
            run_optimizer_job,
            IntervalTrigger(hours=6),
            id='ab_optimizer_job',
            name='A/B Test Auto-Optimizer',
            replace_existing=True
        )
        
        _optimizer_scheduler.start()
        logger.info("🤖 A/B Optimizer scheduler started (runs every 6 hours)")
        
    except Exception as e:
        logger.error(f"Failed to start A/B optimizer scheduler: {e}")


def stop_optimizer_scheduler():
    """Stop the A/B optimizer scheduler"""
    global _optimizer_scheduler
    if _optimizer_scheduler:
        _optimizer_scheduler.shutdown(wait=False)
        _optimizer_scheduler = None
        logger.info("🤖 A/B Optimizer scheduler stopped")


async def run_scheduled_optimization() -> Dict:
    """Run scheduled optimization - checks if enabled first"""
    from config import db
    
    # Check if optimizer is enabled
    config = await db.ab_optimizer_config.find_one({}) or {}
    
    if not config.get("enabled", False):
        return {
            "success": True,
            "skipped": True,
            "reason": "Optimizer is disabled",
            "tests_optimized": 0
        }
    
    # Run the optimizer (not dry run since it's the scheduled job)
    result = await run_auto_optimizer(dry_run=False, min_confidence=config.get("min_confidence", 95.0))
    
    # Log the scheduled run
    await db.ab_optimizer_runs.insert_one({
        "type": "scheduled",
        "timestamp": datetime.now(timezone.utc),
        "tests_checked": result.get("tests_checked", 0),
        "tests_optimized": result.get("tests_optimized", 0),
        "success": result.get("success", False)
    })
    
    return result
