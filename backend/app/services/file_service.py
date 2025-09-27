import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from ..models.responses import TranscriptionFileInfo, TranscriptionListResponse, TranscriptionData


class FileManagementService:
    """Service for managing transcription files and directory operations"""

    def __init__(self):
        # Create transcriptions directory if it doesn't exist
        self.TRANSCRIPTIONS_DIR = Path("transcriptions")
        self.TRANSCRIPTIONS_DIR.mkdir(exist_ok=True)

    def list_transcription_files(self) -> TranscriptionListResponse:
        """List all transcription files"""
        try:
            transcription_files = []
            for file_path in self.TRANSCRIPTIONS_DIR.glob("transcription_*.json"):
                file_stat = file_path.stat()
                transcription_files.append(TranscriptionFileInfo(
                    filename=file_path.name,
                    size_bytes=file_stat.st_size,
                    created=datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
                    modified=datetime.fromtimestamp(file_stat.st_mtime).isoformat()
                ))

            return TranscriptionListResponse(
                transcriptions=sorted(transcription_files, key=lambda x: x.created, reverse=True),
                total_count=len(transcription_files),
                directory=str(self.TRANSCRIPTIONS_DIR)
            )
        except Exception as e:
            return TranscriptionListResponse(
                transcriptions=[],
                total_count=0,
                directory=str(self.TRANSCRIPTIONS_DIR)
            )

    def get_transcription_file(self, filename: str) -> Dict[str, Any]:
        """Retrieve a specific transcription file"""
        try:
            file_path = self.TRANSCRIPTIONS_DIR / filename

            if not file_path.exists():
                return {"error": "Transcription file not found"}

            with open(file_path, "r", encoding="utf-8") as json_file:
                transcription_data = json.load(json_file)

            return transcription_data

        except Exception as e:
            return {"error": str(e)}

    def get_transcriptions_directory(self) -> str:
        """Get the transcriptions directory path"""
        return str(self.TRANSCRIPTIONS_DIR)


# Global instance
file_service = FileManagementService()
