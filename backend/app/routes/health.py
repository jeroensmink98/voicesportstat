from fastapi import APIRouter
from datetime import datetime

from ..models.responses import HealthCheckResponse

router = APIRouter()


@router.get("/", response_model=HealthCheckResponse)
async def read_root():
    """Root endpoint"""
    return HealthCheckResponse(
        status="running",
        timestamp=datetime.now().isoformat()
    )


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint"""
    return HealthCheckResponse(
        status="healthy",
        timestamp=datetime.now().isoformat()
    )
