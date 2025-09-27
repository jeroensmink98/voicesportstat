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
        """Transcribe combined audio using OpenAI Whisper API"""
        temp_file_path = None

        try:
            # Create temporary file for combined audio
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_file_path = self.TRANSCRIPTIONS_DIR / f"temp_audio_{session_id}_{timestamp}.webm"

            # Write audio bytes to temporary file
            with open(temp_file_path, "wb") as temp_file:
                temp_file.write(audio_bytes)

            # Calculate estimated duration
            estimated_duration = chunk_count * 1.0  # 1 second per chunk

            print(f"Transcribing {len(audio_bytes)} bytes using Whisper API...")

            # Try 1: Direct WebM transcription
            try:
                with open(temp_file_path, "rb") as audio_file:
                    print("Trying direct WebM transcription...")
                    response = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        language="en",
                        response_format="verbose_json"
                    )

                transcription_text = response.text
                print(f"✓ Direct WebM transcription successful: {len(transcription_text)} characters")

            except Exception as webm_error:
                print(f"✗ Direct WebM failed: {webm_error}")
                print("Trying conversion approach...")

                # Try 2: Convert to WAV and transcribe
                try:
                    # Import conversion service here to avoid circular imports
                    from .file_conversion_service import FileConversionService

                    conversion_service = FileConversionService()
                    wav_path = temp_file_path.with_suffix('.wav')

                    if await conversion_service.convert_webm_to_wav(temp_file_path, wav_path):
                        print(f"✓ Converted to WAV: {wav_path}")

                        with open(wav_path, "rb") as audio_file:
                            response = client.audio.transcriptions.create(
                                model="whisper-1",
                                file=audio_file,
                                language="en",
                                response_format="verbose_json"
                            )

                        transcription_text = response.text
                        print(f"✓ WAV transcription successful: {len(transcription_text)} characters")

                    else:
                        # Try 3: Convert to MP3 as last resort
                        mp3_path = temp_file_path.with_suffix('.mp3')

                        if await conversion_service.convert_webm_to_mp3(temp_file_path, mp3_path):
                            print(f"✓ Converted to MP3: {mp3_path}")

                            with open(mp3_path, "rb") as audio_file:
                                response = client.audio.transcriptions.create(
                                    model="whisper-1",
                                    file=audio_file,
                                    language="en",
                                    response_format="verbose_json"
                                )

                            transcription_text = response.text
                            print(f"✓ MP3 transcription successful: {len(transcription_text)} characters")

                        else:
                            raise Exception("All conversion methods failed")

                except Exception as conversion_error:
                    print(f"✗ Conversion approach failed: {conversion_error}")
                    raise webm_error

            # Create transcription result
            result = {
                "text": transcription_text,
                "confidence": 0.95,
                "duration": round(estimated_duration, 2),
                "chunk_count": chunk_count,
                "audio_size_bytes": len(audio_bytes),
                "model": "whisper-1",
                "language": response.language if hasattr(response, 'language') else "en",
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
            # Clean up temporary files
            self._cleanup_temp_files(temp_file_path)

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

    def _cleanup_temp_files(self, temp_file_path: Path):
        """Clean up temporary files"""
        if not temp_file_path:
            return

        cleanup_files = [temp_file_path]
        # Also clean up converted files if they were created
        cleanup_files.append(temp_file_path.with_suffix('.wav'))
        cleanup_files.append(temp_file_path.with_suffix('.mp3'))

        for file_path in cleanup_files:
            if file_path and os.path.exists(file_path):
                try:
                    os.unlink(file_path)
                    print(f"Cleaned up temporary file: {file_path}")
                except Exception as cleanup_error:
                    print(f"Warning: Could not clean up {file_path}: {cleanup_error}")


# Global instance
transcription_service = TranscriptionService()
