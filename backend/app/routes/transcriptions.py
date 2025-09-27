from fastapi import APIRouter, HTTPException

from ..services.file_service import file_service
from ..models.responses import TranscriptionListResponse, ErrorResponse

router = APIRouter()


@router.get("/", response_model=TranscriptionListResponse)
async def list_transcriptions():
    """List all transcription files"""
    return file_service.list_transcription_files()


@router.get("/{filename}", response_model=dict)
async def get_transcription(filename: str):
    """Retrieve a specific transcription file"""
    result = file_service.get_transcription_file(filename)

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result
