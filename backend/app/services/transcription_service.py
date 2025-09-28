import os
import logging
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
        self.logger = logging.getLogger(__name__)
        # Create transcriptions directory if it doesn't exist
        self.TRANSCRIPTIONS_DIR = Path("transcriptions")
        self.TRANSCRIPTIONS_DIR.mkdir(exist_ok=True)

    async def transcribe_audio(self, audio_bytes: bytes, session_id: str, chunk_count: int, language: str = "en") -> Dict[str, Any]:
        """Transcribe WAV bytes using OpenAI Whisper API. Assumes bytes are valid WAV."""
        self.logger.debug(f"transcribe_audio called with language: {language} for session: {session_id}")
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
                    self.logger.debug(f"WAV diagnostics: channels={wf.getnchannels()} sampwidth={wf.getsampwidth()} framerate={wf.getframerate()} frames={frames} duration~{estimated_duration:.2f}s")
            except Exception as diag_err:
                self.logger.warning(f"WAV diagnostics failed: {diag_err}")
                estimated_duration = chunk_count * 0.25

            self.logger.info(f"Transcribing {len(audio_bytes)} bytes (estimated {estimated_duration:.2f}s) using Whisper API...")

            # Transcribe
            with open(temp_wav_path, "rb") as audio_file:
                response = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=language,
                    response_format="verbose_json"
                )

            transcription_text = response.text
            self.logger.info(f"WAV transcription successful: {len(transcription_text)} characters")

            # Create transcription result
            detected_language = getattr(response, 'language', None)
            self.logger.debug(f"Using language '{language}' for result (detected: {detected_language})")
            result = {
                "text": transcription_text,
                "confidence": 0.95,
                "duration": round(float(estimated_duration or (chunk_count * 0.25)), 2),
                "chunk_count": chunk_count,
                "audio_size_bytes": len(audio_bytes),
                "model": "whisper-1",
                "language": language,  # Use the language parameter passed from the session
                "detected_language": detected_language,  # Store detected language separately if needed
                "timestamp": datetime.now().isoformat()
            }

            # Save transcription to JSON file
            await self.save_transcription_to_json(result, session_id, timestamp, language)

            self.logger.info(f"Transcription complete: {len(transcription_text)} characters")
            return result

        except Exception as e:
            self.logger.error(f"Error in Whisper transcription: {e}")

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

    async def save_transcription_to_json(self, transcription_result: Dict[str, Any], session_id: str, timestamp: str, language: str = "en"):
        """Save transcription result to session JSON file (accumulate all transcriptions for the session)"""
        try:
            # Create filename with only session_id (one file per session)
            filename = f"transcription_session_{session_id}.json"
            filepath = self.TRANSCRIPTIONS_DIR / filename

            # Prepare transcription data for this batch
            transcription_data = {
                "timestamp": transcription_result["timestamp"],
                "text": transcription_result["text"],
                "confidence": transcription_result["confidence"],
                "duration_seconds": transcription_result["duration"],
                "chunk_count": transcription_result["chunk_count"],
                "audio_size_bytes": transcription_result["audio_size_bytes"],
                "model": transcription_result.get("model", "whisper-1"),
                "language": language,  # Use the language passed from the session
                "processing_timestamp": datetime.now().isoformat(),
                "ready_for_llm": True
            }

            # Add error info if present
            if "error" in transcription_result:
                transcription_data["error"] = transcription_result["error"]

            import json

            # Check if session file already exists
            if filepath.exists():
                # Read existing session data
                try:
                    with open(filepath, "r", encoding="utf-8") as json_file:
                        session_data = json.load(json_file)
                except json.JSONDecodeError:
                    self.logger.warning(f"Existing session file {filepath} is corrupted, creating new one")
                    session_data = None
            else:
                session_data = None

            if session_data:
                # Append to existing session
                if "transcriptions" not in session_data:
                    # Convert old format to new format
                    session_data["transcriptions"] = [session_data.pop("transcription", {})]
                    session_data["transcriptions"][0]["timestamp"] = session_data.get("timestamp", transcription_result["timestamp"])
                    session_data["transcriptions"][0]["processing_timestamp"] = session_data.get("processing_timestamp", datetime.now().isoformat())
                    session_data["transcriptions"][0]["language"] = session_data["transcriptions"][0].get("language", language)

                # Add new transcription
                session_data["transcriptions"].append(transcription_data)
                session_data["last_updated"] = datetime.now().isoformat()
                session_data["language"] = language  # Update session language if it changed
            else:
                # Create new session file
                session_data = {
                    "session_id": session_id,
                    "created_at": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat(),
                    "language": language,
                    "transcriptions": [transcription_data]
                }

            # Write updated session data back to file
            with open(filepath, "w", encoding="utf-8") as json_file:
                json.dump(session_data, json_file, indent=2, ensure_ascii=False)

            self.logger.info(f"Transcription saved to session file: {filepath} (total transcriptions: {len(session_data['transcriptions'])})")

        except Exception as e:
            self.logger.error(f"Error saving transcription to JSON: {e}")

    def _cleanup_temp_files(self, wav_path: Path):
        """Clean up temporary WAV file"""
        if wav_path and os.path.exists(wav_path):
            try:
                os.unlink(wav_path)
                self.logger.debug(f"Cleaned up temporary file: {wav_path}")
            except Exception as cleanup_error:
                self.logger.warning(f"Could not clean up {wav_path}: {cleanup_error}")


# Global instance
transcription_service = TranscriptionService()
