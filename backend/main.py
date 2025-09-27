from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Config
from app.routes import health_router, transcriptions_router, audio_router

# Create FastAPI application
app = FastAPI(title="VoiceSportStat Backend")

# Add CORS middleware to allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    health_router,
    prefix="",
    tags=["health"]
)

app.include_router(
    transcriptions_router,
    prefix="/transcriptions",
    tags=["transcriptions"]
)

app.include_router(
    audio_router,
    prefix="",
    tags=["audio"]
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)