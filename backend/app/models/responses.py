from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str


class TranscriptionFileInfo(BaseModel):
    """Information about a transcription file"""
    filename: str
    size_bytes: int
    created: str
    modified: str


class TranscriptionListResponse(BaseModel):
    """Response for listing transcriptions"""
    transcriptions: List[TranscriptionFileInfo]
    total_count: int
    directory: str


class TranscriptionData(BaseModel):
    """Transcription data structure"""
    session_id: str
    timestamp: str
    transcription: dict
    metadata: dict
    error: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
