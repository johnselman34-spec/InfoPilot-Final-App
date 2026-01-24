"""
Stats Router - InfoPilot Explorer
Handles statistics, analytics, and map data endpoints
"""

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Optional, Dict
from datetime import datetime, timezone
import os
import re

router = APIRouter(prefix="/stats", tags=["Statistics"])

# Database connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'infopilot_explorer')]

# US Region mapping
US_REGIONS = {
    "Northeast": ["Connecticut", "Maine", "Massachusetts", "New Hampshire", "Rhode Island", 
                  "Vermont", "New Jersey", "New York", "Pennsylvania"],
    "Midwest": ["Illinois", "Indiana", "Michigan", "Ohio", "Wisconsin", "Iowa", "Kansas",
                "Minnesota", "Missouri", "Nebraska", "North Dakota", "South Dakota"],
    "South": ["Delaware", "Florida", "Georgia", "Maryland", "North Carolina", "South Carolina",
              "Virginia", "District of Columbia", "West Virginia", "Alabama", "Kentucky",
              "Mississippi", "Tennessee", "Arkansas", "Louisiana", "Oklahoma", "Texas"],
    "West": ["Arizona", "Colorado", "Idaho", "Montana", "Nevada", "New Mexico", "Utah",
             "Wyoming", "Alaska", "California", "Hawaii", "Oregon", "Washington"]
}


def get_region_for_state(state: str) -> str:
    """Get US region for a state"""
    for region, states in US_REGIONS.items():
        if state in states:
            return region
    return "Unknown"


@router.get("/overview")
async def get_stats_overview(user_id: str = None):
    """Get comprehensive statistics overview"""
    
    # Total counts
    total_results = await db.search_results.count_documents({"user_id": user_id})
    total_categories = await db.categories.count_documents({"user_id": user_id})
    
    # Count locations
    results_with_locations = await db.search_results.find(
        {"user_id": user_id, "locations": {"$exists": True, "$ne": []}},
        {"locations": 1}
    ).to_list(10000)
    
    total_locations = sum(len(r.get("locations", [])) for r in results_with_locations)
    
    # By document type
    by_document_type = await db.search_results.aggregate([
        {"$match": {"user_id": user_id}},
        {"$group": {"_id": "$document_type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]).to_list(20)
    
    # By source type (domain categories)
    by_source_type = await db.search_results.aggregate([
        {"$match": {"user_id": user_id}},
        {"$addFields": {
            "source_type": {
                "$switch": {
                    "branches": [
                        {"case": {"$regexMatch": {"input": "$root_domain", "regex": "edu$"}}, "then": "Educational"},
                        {"case": {"$regexMatch": {"input": "$root_domain", "regex": "gov$"}}, "then": "Government"},
                        {"case": {"$regexMatch": {"input": "$root_domain", "regex": "org$"}}, "then": "Organization"},
                        {"case": {"$regexMatch": {"input": "$root_domain", "regex": "wikipedia"}}, "then": "Wikipedia"},
                        {"case": {"$regexMatch": {"input": "$root_domain", "regex": "news|cnn|bbc|nyt"}}, "then": "News"}
                    ],
                    "default": "Commercial"
                }
            }
        }},
        {"$group": {"_id": "$source_type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]).to_list(20)
    
    # By category
    by_category = await db.search_results.aggregate([
        {"$match": {"user_id": user_id}},
        {"$unwind": "$category_ids"},
        {"$lookup": {
            "from": "categories",
            "localField": "category_ids",
            "foreignField": "category_id",
            "as": "category"
        }},
        {"$unwind": {"path": "$category", "preserveNullAndEmptyArrays": True}},
        {"$group": {"_id": {"$ifNull": ["$category.name", "$category_ids"]}, "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]).to_list(50)
    
    # By reaction
    by_reaction = await db.search_results.aggregate([
        {"$match": {"user_id": user_id}},
        {"$project": {"reactions": {"$objectToArray": "$reactions"}}},
        {"$unwind": "$reactions"},
        {"$group": {"_id": "$reactions.k", "count": {"$sum": "$reactions.v"}}},
        {"$sort": {"count": -1}}
    ]).to_list(20)
    
    # By country
    by_country = await db.search_results.aggregate([
        {"$match": {"user_id": user_id, "locations": {"$exists": True, "$ne": []}}},
        {"$unwind": "$locations"},
        {"$group": {"_id": "$locations.country", "count": {"$sum": 1}}},
        {"$match": {"_id": {"$ne": None}}},
        {"$sort": {"count": -1}}
    ]).to_list(50)
    
    # By state
    by_state = await db.search_results.aggregate([
        {"$match": {"user_id": user_id, "locations": {"$exists": True, "$ne": []}}},
        {"$unwind": "$locations"},
        {"$group": {"_id": "$locations.state", "count": {"$sum": 1}}},
        {"$match": {"_id": {"$ne": None}}},
        {"$sort": {"count": -1}}
    ]).to_list(50)
    
    # By city
    by_city = await db.search_results.aggregate([
        {"$match": {"user_id": user_id, "locations": {"$exists": True, "$ne": []}}},
        {"$unwind": "$locations"},
        {"$group": {"_id": "$locations.city", "count": {"$sum": 1}}},
        {"$match": {"_id": {"$ne": None}}},
        {"$sort": {"count": -1}}
    ]).to_list(50)
    
    # By US region
    region_counts = {region: 0 for region in US_REGIONS.keys()}
    for state_data in by_state:
        state = state_data.get("_id")
        if state:
            region = get_region_for_state(state)
            if region in region_counts:
                region_counts[region] += state_data.get("count", 0)
    
    by_region = [{"_id": k, "count": v} for k, v in region_counts.items() if v > 0]
    
    # By year
    by_year = await db.search_results.aggregate([
        {"$match": {"user_id": user_id, "year": {"$exists": True, "$ne": None}}},
        {"$group": {"_id": "$year", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]).to_list(100)
    
    # By domain
    by_domain = await db.search_results.aggregate([
        {"$match": {"user_id": user_id}},
        {"$group": {"_id": "$root_domain", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]).to_list(50)
    
    # By TLD
    by_tld = await db.search_results.aggregate([
        {"$match": {"user_id": user_id}},
        {"$addFields": {"tld": {"$arrayElemAt": [{"$split": ["$root_domain", "."]}, -1]}}},
        {"$group": {"_id": "$tld", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]).to_list(20)
    
    # By day of week
    by_day_of_week = await db.search_results.aggregate([
        {"$match": {"user_id": user_id}},
        {"$addFields": {"day": {"$dayOfWeek": {"$toDate": "$collated_at"}}}},
        {"$group": {"_id": "$day", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]).to_list(7)
    
    day_names = {1: "Sun", 2: "Mon", 3: "Tue", 4: "Wed", 5: "Thu", 6: "Fri", 7: "Sat"}
    by_day_of_week = [{"_id": day_names.get(d["_id"], d["_id"]), "count": d["count"]} for d in by_day_of_week]
    
    # By month
    by_month = await db.search_results.aggregate([
        {"$match": {"user_id": user_id}},
        {"$addFields": {"month": {"$month": {"$toDate": "$collated_at"}}}},
        {"$group": {"_id": "$month", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]).to_list(12)
    
    month_names = {1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
                   7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"}
    by_month = [{"_id": month_names.get(m["_id"], m["_id"]), "count": m["count"]} for m in by_month]
    
    return {
        "total_results": total_results,
        "total_categories": total_categories,
        "total_locations": total_locations,
        "by_document_type": by_document_type,
        "by_source_type": by_source_type,
        "by_category": by_category,
        "by_reaction": by_reaction,
        "by_country": by_country,
        "by_state": by_state,
        "by_city": by_city,
        "by_region": by_region,
        "by_year": by_year,
        "by_domain": by_domain,
        "by_tld": by_tld,
        "by_day_of_week": by_day_of_week,
        "by_month": by_month
    }


@router.get("/map-data-detailed")
async def get_detailed_map_data(user_id: str = None):
    """Get detailed map data with all results per location"""
    results = await db.search_results.find(
        {"user_id": user_id, "locations": {"$exists": True, "$ne": []}},
        {"_id": 0}
    ).to_list(1000)
    
    location_groups = {}
    for result in results:
        for loc in result.get("locations", []):
            key = f"{loc.get('country', 'Unknown')}_{loc.get('state', '')}_{loc.get('city', '')}"
            if key not in location_groups:
                location_groups[key] = {
                    "location": loc,
                    "results": [],
                    "count": 0
                }
            location_groups[key]["results"].append({
                "result_id": result.get("result_id"),
                "title": result.get("title"),
                "url": result.get("url"),
                "document_type": result.get("document_type"),
                "snippet": result.get("snippet", "")[:200]
            })
            location_groups[key]["count"] += 1
    
    return {
        "locations": list(location_groups.values()),
        "total_locations": len(location_groups),
        "total_results": len(results)
    }


@router.get("/map-location/{location_key}")
async def get_results_by_location(
    location_key: str,
    page: int = 1,
    limit: int = 20,
    user_id: str = None
):
    """Get all search results for a specific map location"""
    parts = location_key.split("_")
    country = parts[0] if len(parts) > 0 else None
    state = parts[1] if len(parts) > 1 else None
    city = parts[2] if len(parts) > 2 else None
    
    query = {"user_id": user_id}
    
    if country:
        query["locations.country"] = country
    if state:
        query["locations.state"] = state
    if city:
        query["locations.city"] = city
    
    skip = (page - 1) * limit
    
    results = await db.search_results.find(
        query,
        {"_id": 0}
    ).sort("collated_at", -1).skip(skip).limit(limit).to_list(limit)
    
    total = await db.search_results.count_documents(query)
    
    return {
        "results": results,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit
    }
