"""
Voice Service - OpenAI Whisper Integration for Speech-to-Text
Uses Emergent LLM Key for voice search functionality
"""
import os
import tempfile
import logging
from dotenv import load_dotenv
from emergentintegrations.llm.openai import OpenAISpeechToText

load_dotenv()
logger = logging.getLogger(__name__)

class VoiceService:
    """Voice Service for speech-to-text transcription using OpenAI Whisper"""
    
    @staticmethod
    async def transcribe_audio(audio_data: bytes, filename: str = "audio.webm") -> dict:
        """
        Transcribe audio data to text using OpenAI Whisper
        
        Args:
            audio_data: Raw audio bytes
            filename: Original filename to determine format
            
        Returns:
            dict with transcription results
        """
        try:
            api_key = os.getenv("EMERGENT_LLM_KEY")
            if not api_key:
                raise ValueError("EMERGENT_LLM_KEY not found in environment")
            
            # Initialize Whisper STT
            stt = OpenAISpeechToText(api_key=api_key)
            
            # Determine file extension
            ext = filename.split('.')[-1].lower() if '.' in filename else 'webm'
            if ext not in ['mp3', 'mp4', 'mpeg', 'mpga', 'm4a', 'wav', 'webm']:
                ext = 'webm'  # Default to webm for browser recordings
            
            # Write to temp file
            with tempfile.NamedTemporaryFile(suffix=f'.{ext}', delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_path = temp_file.name
            
            try:
                # Transcribe
                with open(temp_path, 'rb') as audio_file:
                    response = await stt.transcribe(
                        file=audio_file,
                        model="whisper-1",
                        response_format="verbose_json",
                        language="en",
                        temperature=0.0
                    )
                
                # Extract text and metadata
                result = {
                    "success": True,
                    "text": response.text if hasattr(response, 'text') else str(response),
                    "language": getattr(response, 'language', 'en'),
                    "duration": getattr(response, 'duration', None),
                    "segments": []
                }
                
                # Add segments if available
                if hasattr(response, 'segments'):
                    result["segments"] = [
                        {
                            "start": seg.start,
                            "end": seg.end,
                            "text": seg.text
                        }
                        for seg in response.segments
                    ]
                
                logger.info(f"Transcribed audio: {result['text'][:100]}...")
                return result
                
            finally:
                # Cleanup temp file
                try:
                    os.unlink(temp_path)
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Voice transcription failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": ""
            }
    
    @staticmethod
    async def transcribe_file(file_path: str) -> dict:
        """
        Transcribe an audio file from disk
        
        Args:
            file_path: Path to audio file
            
        Returns:
            dict with transcription results
        """
        try:
            with open(file_path, 'rb') as f:
                audio_data = f.read()
            
            return await VoiceService.transcribe_audio(audio_data, os.path.basename(file_path))
            
        except Exception as e:
            logger.error(f"File transcription failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "text": ""
            }
