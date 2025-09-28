import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
def setup_logging():
    """Configure application logging"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Reduce noise from external libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

# Set up logging
setup_logging()

# Create a logger instance for the config module
logger = logging.getLogger(__name__)

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
