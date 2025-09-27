import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
class Config:
    """Application configuration"""

    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # CORS Configuration
    CORS_ORIGINS = [
        "http://localhost:5173",  # SvelteKit dev
        "http://localhost:4173",  # SvelteKit preview
    ]

    # Batch Processing Configuration
    BATCH_SIZE_SECONDS = 5  # Process every 5 seconds of audio
    MIN_CHUNKS_FOR_BATCH = 5   # Minimum chunks before processing
    MAX_CHUNKS_FOR_BATCH = 20  # Maximum chunks before forcing processing

    # File Paths
    TRANSCRIPTIONS_DIR = Path("transcriptions")


# Create transcriptions directory if it doesn't exist
Config.TRANSCRIPTIONS_DIR.mkdir(exist_ok=True)
