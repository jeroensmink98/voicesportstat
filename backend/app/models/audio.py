from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class AudioChunk(BaseModel):
    """Represents a single audio chunk received from the frontend"""
    data: List[int]  # Base64 encoded audio data as array of integers
    timestamp: Optional[str] = None
    sequenceNumber: int
    mimeType: str = "audio/wav"


class WebSocketMessage(BaseModel):
    """WebSocket message structure"""
    type: str
    data: Optional[List[int]] = None
    timestamp: Optional[str] = None
    sequenceNumber: Optional[int] = None
    mimeType: Optional[str] = None
    language: Optional[str] = None


class AudioSession(BaseModel):
    """Audio session information"""
    session_id: str
    chunks: List[AudioChunk]
    start_time: datetime
    last_processed: datetime
    total_chunks: int
    websocket: Any  # WebSocket connection object
    language: str = "en"  # Language code for transcription


class TranscriptionResult(BaseModel):
    """Result of audio transcription"""
    text: str
    confidence: float
    duration: float
    chunk_count: int
    audio_size_bytes: int
    model: str = "whisper-1"
    language: str = "en"
    timestamp: str
    error: Optional[str] = None


class TranscriptionResponse(BaseModel):
    """Response sent back to client with transcription"""
    type: str = "batch_transcription"
    text: str
    confidence: float
    chunk_count: int
    duration_seconds: float
    timestamp: str
    ready_for_llm: bool = True


class RecordingCompleteInfo(BaseModel):
    """Information about completed recording session"""
    type: str = "recording_complete"
    message: str
    total_chunks_processed: int
    timestamp: str
