import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
openai.api_key = os.getenv("OPENAI_API_KEY")
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class TranscriptionService:
    """Service for handling audio transcription using OpenAI Whisper"""

    def __init__(self):
        # Create transcriptions directory if it doesn't exist
        self.TRANSCRIPTIONS_DIR = Path("transcriptions")
        self.TRANSCRIPTIONS_DIR.mkdir(exist_ok=True)

    async def transcribe_audio(self, audio_bytes: bytes, session_id: str, chunk_count: int) -> Dict[str, Any]:
        """Transcribe WAV bytes using OpenAI Whisper API. Assumes bytes are valid WAV."""
        temp_wav_path = None

        try:
            # Create temporary WAV file for this batch
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_wav_path = self.TRANSCRIPTIONS_DIR / f"temp_audio_{session_id}_{timestamp}.wav"

            with open(temp_wav_path, "wb") as wav_file:
                wav_file.write(audio_bytes)

            # Basic diagnostics: read WAV params to estimate duration
            estimated_duration = None
            try:
                import wave, contextlib
                with contextlib.closing(wave.open(str(temp_wav_path), 'rb')) as wf:
                    frames = wf.getnframes()
                    rate = wf.getframerate() or 16000
                    estimated_duration = frames / float(rate)
                    print(f"WAV diagnostics: channels={wf.getnchannels()} sampwidth={wf.getsampwidth()} framerate={wf.getframerate()} frames={frames} duration~{estimated_duration:.2f}s")
            except Exception as diag_err:
                print(f"WAV diagnostics failed: {diag_err}")
                estimated_duration = chunk_count * 0.25

            print(f"Transcribing {len(audio_bytes)} bytes (estimated {estimated_duration:.2f}s) using Whisper API...")

            # Transcribe
            with open(temp_wav_path, "rb") as audio_file:
                response = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="en",
                    response_format="verbose_json"
                )

            transcription_text = response.text
            print(f"✓ WAV transcription successful: {len(transcription_text)} characters")

            # Create transcription result
            result = {
                "text": transcription_text,
                "confidence": 0.95,
                "duration": round(float(estimated_duration or (chunk_count * 0.25)), 2),
                "chunk_count": chunk_count,
                "audio_size_bytes": len(audio_bytes),
                "model": "whisper-1",
                "language": getattr(response, 'language', 'en') or 'en',
                "timestamp": datetime.now().isoformat()
            }

            # Save transcription to JSON file
            await self.save_transcription_to_json(result, session_id, timestamp)

            print(f"Transcription complete: {len(transcription_text)} characters")
            return result

        except Exception as e:
            print(f"Error in Whisper transcription: {e}")

            # Return error result
            return {
                "text": f"[Transcription Error: {str(e)}]",
                "confidence": 0.0,
                "duration": chunk_count * 1.0,
                "chunk_count": chunk_count,
                "audio_size_bytes": len(audio_bytes),
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        finally:
            # Clean up temporary WAV file
            self._cleanup_temp_files(temp_wav_path)

    async def save_transcription_to_json(self, transcription_result: Dict[str, Any], session_id: str, timestamp: str):
        """Save transcription result to JSON file"""
        try:
            # Create filename with session and timestamp
            filename = f"transcription_{session_id}_{timestamp}.json"
            filepath = self.TRANSCRIPTIONS_DIR / filename

            # Prepare data for JSON file
            json_data = {
                "session_id": session_id,
                "timestamp": transcription_result["timestamp"],
                "transcription": {
                    "text": transcription_result["text"],
                    "confidence": transcription_result["confidence"],
                    "duration_seconds": transcription_result["duration"],
                    "chunk_count": transcription_result["chunk_count"],
                    "audio_size_bytes": transcription_result["audio_size_bytes"]
                },
                "metadata": {
                    "model": transcription_result.get("model", "whisper-1"),
                    "language": transcription_result.get("language", "en"),
                    "processing_timestamp": datetime.now().isoformat(),
                    "ready_for_llm": True
                }
            }

            # Add error info if present
            if "error" in transcription_result:
                json_data["error"] = transcription_result["error"]

            # Write to JSON file
            import json
            with open(filepath, "w", encoding="utf-8") as json_file:
                json.dump(json_data, json_file, indent=2, ensure_ascii=False)

            print(f"Transcription saved to: {filepath}")

        except Exception as e:
            print(f"Error saving transcription to JSON: {e}")

    def _cleanup_temp_files(self, wav_path: Path):
        """Clean up temporary WAV file"""
        if wav_path and os.path.exists(wav_path):
            try:
                os.unlink(wav_path)
                print(f"Cleaned up temporary file: {wav_path}")
            except Exception as cleanup_error:
                print(f"Warning: Could not clean up {wav_path}: {cleanup_error}")


# Global instance
transcription_service = TranscriptionService()
