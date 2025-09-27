from .health import router as health_router
from .transcriptions import router as transcriptions_router
from .audio import router as audio_router

__all__ = [
    "health_router",
    "transcriptions_router",
    "audio_router"
]
