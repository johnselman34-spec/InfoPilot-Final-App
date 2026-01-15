"""
InfoPilot Explorer - Voice Search Routes
Speech-to-text using OpenAI Whisper for voice search
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from datetime import datetime, timezone
from typing import Optional
import logging

from config import db, logger
from routes.auth import get_current_user
from services.voice_service import VoiceService

router = APIRouter(tags=["Voice Search"])


@router.post("/voice/transcribe", response_model=dict)
async def transcribe_audio(
    audio: UploadFile = File(...),
    user = Depends(get_current_user)
):
    """
    Transcribe audio to text for voice search
    
    Supports: mp3, mp4, mpeg, mpga, m4a, wav, webm
    Max size: 25MB
    """
    # Validate file size (25MB max for Whisper)
    MAX_SIZE = 25 * 1024 * 1024
    
    # Read file
    audio_data = await audio.read()
    
    if len(audio_data) > MAX_SIZE:
        raise HTTPException(
            status_code=400,
            detail="Audio file exceeds 25MB limit"
        )
    
    # Validate file type
    filename = audio.filename or "audio.webm"
    ext = filename.split('.')[-1].lower() if '.' in filename else 'webm'
    valid_formats = ['mp3', 'mp4', 'mpeg', 'mpga', 'm4a', 'wav', 'webm']
    
    if ext not in valid_formats:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format. Supported: {', '.join(valid_formats)}"
        )
    
    # Transcribe
    result = await VoiceService.transcribe_audio(audio_data, filename)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=500,
            detail=result.get("error", "Transcription failed")
        )
    
    # Log voice search for analytics
    await db.voice_searches.insert_one({
        "user_id": str(user["_id"]),
        "transcription": result["text"],
        "duration": result.get("duration"),
        "language": result.get("language", "en"),
        "created_at": datetime.now(timezone.utc)
    })
    
    return {
        "success": True,
        "text": result["text"],
        "language": result.get("language", "en"),
        "duration": result.get("duration"),
        "segments": result.get("segments", [])
    }


@router.post("/voice/search", response_model=dict)
async def voice_search(
    audio: UploadFile = File(...),
    user = Depends(get_current_user)
):
    """
    Voice search - transcribe audio and perform search
    Returns transcription and search results
    """
    from services.search_service import WebSearchService
    
    # Transcribe audio
    audio_data = await audio.read()
    filename = audio.filename or "audio.webm"
    
    transcription = await VoiceService.transcribe_audio(audio_data, filename)
    
    if not transcription.get("success"):
        raise HTTPException(
            status_code=500,
            detail=transcription.get("error", "Transcription failed")
        )
    
    query = transcription["text"]
    
    if not query.strip():
        return {
            "transcription": "",
            "results": [],
            "message": "No speech detected"
        }
    
    # Perform search
    try:
        search_results = await WebSearchService.search(query, max_results=20)
        
        formatted_results = []
        for r in search_results:
            formatted_results.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": r.get("snippet", ""),
                "article_type": WebSearchService.classify_article_type(
                    r.get("url", ""), r.get("title", ""), r.get("content", "")
                ),
                "root_domain": WebSearchService.extract_root_domain(r.get("url", ""))
            })
        
        # Log voice search
        await db.voice_searches.insert_one({
            "user_id": str(user["_id"]),
            "transcription": query,
            "result_count": len(formatted_results),
            "search_performed": True,
            "created_at": datetime.now(timezone.utc)
        })
        
        return {
            "transcription": query,
            "results": formatted_results,
            "result_count": len(formatted_results)
        }
        
    except Exception as e:
        logger.error(f"Voice search failed: {e}")
        return {
            "transcription": query,
            "results": [],
            "error": str(e)
        }


@router.get("/voice/history", response_model=dict)
async def get_voice_search_history(
    limit: int = 20,
    user = Depends(get_current_user)
):
    """Get user's voice search history"""
    searches = await db.voice_searches.find({
        "user_id": str(user["_id"])
    }).sort("created_at", -1).limit(limit).to_list(limit)
    
    return {
        "searches": [{
            "id": str(s["_id"]),
            "transcription": s["transcription"],
            "duration": s.get("duration"),
            "result_count": s.get("result_count"),
            "created_at": s.get("created_at", datetime.now(timezone.utc)).isoformat()
        } for s in searches]
    }


@router.get("/voice/stats", response_model=dict)
async def get_voice_stats(user = Depends(get_current_user)):
    """Get voice search statistics (admin only)"""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    total_searches = await db.voice_searches.count_documents({})
    unique_users = len(await db.voice_searches.distinct("user_id"))
    
    # Get top transcriptions
    pipeline = [
        {"$group": {"_id": "$transcription", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    top_queries = await db.voice_searches.aggregate(pipeline).to_list(10)
    
    return {
        "total_searches": total_searches,
        "unique_users": unique_users,
        "top_queries": [{"query": q["_id"], "count": q["count"]} for q in top_queries]
    }
