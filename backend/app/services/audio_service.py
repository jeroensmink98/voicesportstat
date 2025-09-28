import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path
import wave
import io
from typing import Optional

import ffmpeg

from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from ..models.audio import (
    AudioChunk, AudioSession, WebSocketMessage,
    TranscriptionResult, TranscriptionResponse, RecordingCompleteInfo
)
from .azure_blob_service import azure_blob_service


class AudioProcessingService:
    """Service for handling audio processing, WebSocket connections, and batch processing"""

    def __init__(self):
        # Set up logger
        self.logger = logging.getLogger(__name__)
        # Global storage for audio sessions
        self.audio_sessions: Dict[str, Dict[str, Any]] = {}

        # Batch processing configuration
        self.BATCH_SIZE_SECONDS = 5  # Process every 5 seconds of audio
        self.MIN_CHUNKS_FOR_BATCH = 5   # Minimum chunks before processing
        self.MAX_CHUNKS_FOR_BATCH = 20  # Maximum chunks before forcing processing

        # Create transcriptions directory if it doesn't exist
        self.TRANSCRIPTIONS_DIR = Path("transcriptions")
        self.TRANSCRIPTIONS_DIR.mkdir(exist_ok=True)

        # Target PCM/WAV parameters
        self.TARGET_SAMPLE_RATE = 16000
        self.TARGET_CHANNELS = 1
        self.TARGET_SAMPLE_WIDTH = 2  # bytes (16-bit)

    def _decode_to_pcm(self, audio_bytes: bytes, mime_type: Optional[str]) -> bytes:
        """Decode an input chunk (WAV or WebM/Opus) to PCM S16LE 16k mono using ffmpeg."""
        if not audio_bytes:
            return b""

        declared_format: Optional[str] = None
        try:
            if mime_type:
                mime_lower = mime_type.lower()
                if "webm" in mime_lower:
                    declared_format = "webm"
                elif "wav" in mime_lower:
                    declared_format = "wav"

            def run_ffmpeg(input_bytes: bytes, force_format: Optional[str]) -> bytes:
                input_kwargs = {"f": force_format} if force_format else {}
                stream = (
                    ffmpeg
                    .input("pipe:0", **input_kwargs)
                    .output(
                        "pipe:1",
                        f="s16le",
                        acodec="pcm_s16le",
                        ar=self.TARGET_SAMPLE_RATE,
                        ac=self.TARGET_CHANNELS,
                    )
                    .overwrite_output()
                )
                out, err = ffmpeg.run(stream, input=input_bytes, capture_stdout=True, capture_stderr=True)
                return out

            # First attempt: use declared input format if available
            try:
                return run_ffmpeg(audio_bytes, declared_format)
            except ffmpeg.Error:
                # Fallback: let ffmpeg auto-detect
                return run_ffmpeg(audio_bytes, None)

        except ffmpeg.Error as e:
            preview = e.stderr.decode("utf-8", errors="ignore")[:500] if getattr(e, "stderr", None) else str(e)
            raise RuntimeError(f"ffmpeg decode error ({declared_format or 'auto'}): {preview}")

    def _wav_from_pcm(self, pcm_bytes: bytes) -> bytes:
        """Wrap raw PCM S16LE 16k mono bytes into a proper WAV container and return bytes."""
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(self.TARGET_CHANNELS)
            wav_file.setsampwidth(self.TARGET_SAMPLE_WIDTH)
            wav_file.setframerate(self.TARGET_SAMPLE_RATE)
            wav_file.writeframes(pcm_bytes)
        return buffer.getvalue()

    async def handle_websocket_connection(self, websocket: WebSocket):
        """Handle WebSocket connection for audio streaming"""
        await websocket.accept()

        # Create unique session ID
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(websocket)}"

        try:
            # Initialize session
            self.audio_sessions[session_id] = {
                "chunks": [],
                "start_time": datetime.now(),
                "last_processed": datetime.now(),
                "total_chunks": 0,
                "websocket": websocket,
                "language": "en",  # Default language
                # PCM aggregation state
                "pcm_buffer": bytearray(),
                "last_batch_offset": 0,
                "source_mime_type": None,
                # For WebM/Opus sources we keep container bytes and decode at batch time
                "webm_buffer": bytearray(),
                "processed_pcm_offset": 0,
                # Aggregate buffers so we can rebuild the full session audio upon completion
                "full_pcm_buffer": bytearray(),
            }

            # Send welcome message
            await websocket.send_text(json.dumps({
                "type": "connection",
                "message": "WebSocket connected successfully",
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }))

            self.logger.info(f"WebSocket connection established for session {session_id} at {datetime.now()}")

            while True:
                try:
                    # Receive audio chunk data from frontend
                    data = await websocket.receive_text()
                    message = json.loads(data)

                    if message.get("type") == "audio_chunk":
                        # Process audio chunk with batch logic
                        await self.process_audio_chunk_batch(websocket, session_id, message)
                    elif message.get("type") == "start_recording":
                        # Store language information for the session
                        session_language = message.get("language", "en")
                        self.logger.debug(f"Received start_recording with language: {session_language}")
                        self.logger.debug(f"Session ID: {session_id}")
                        self.logger.debug(f"Sessions available: {list(self.audio_sessions.keys())}")

                        if session_id in self.audio_sessions:
                            old_language = self.audio_sessions[session_id].get("language", "en")
                            self.audio_sessions[session_id]["language"] = session_language
                            new_language = self.audio_sessions[session_id].get("language", "en")
                            self.logger.debug(f"Updated session language from {old_language} to {new_language}")
                            await websocket.send_text(json.dumps({
                                "type": "recording_started",
                                "message": f"Recording session started with language: {session_language}",
                                "language": session_language,
                                "timestamp": datetime.now().isoformat()
                            }))
                        else:
                            self.logger.debug(f"Session {session_id} not found in audio_sessions")
                    elif message.get("type") == "end_recording":
                        # Process final batch
                        await self.process_final_batch(session_id)
                        break
                    else:
                        # Handle other message types
                        await self.handle_other_messages(websocket, message)

                except WebSocketDisconnect:
                    self.logger.info(f"WebSocket disconnected for session {session_id} at {datetime.now()}")
                    break
                except json.JSONDecodeError as e:
                    self.logger.warning(f"JSON decode error: {e}")
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Invalid JSON format",
                        "timestamp": datetime.now().isoformat()
                    }))
                except Exception as e:
                    self.logger.error(f"Error processing message: {e}")
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": f"Server error: {str(e)}",
                        "timestamp": datetime.now().isoformat()
                    }))

        except WebSocketDisconnect:
            self.logger.info(f"WebSocket connection closed for session {session_id} at {datetime.now()}")
        except Exception as e:
            self.logger.error(f"WebSocket error: {e}")
        finally:
            await self.finalize_session_recording(session_id)
            # Cleanup session
            if session_id in self.audio_sessions:
                del self.audio_sessions[session_id]

    async def process_audio_chunk_batch(self, websocket: WebSocket, session_id: str, message: Dict[str, Any]):
        """Process incoming audio chunk and manage batch processing"""
        try:
            # Extract audio data
            audio_data = message.get("data", [])
            timestamp = message.get("timestamp")
            sequence_number = message.get("sequenceNumber")
            mime_type = message.get("mimeType", "audio/wav")

            # Convert bytes array back to bytes
            audio_bytes = bytes(audio_data)

            self.logger.debug(f"Session {session_id} - Received chunk {sequence_number}: {len(audio_bytes)} bytes")

            # Add chunk to session
            if session_id in self.audio_sessions:
                session = self.audio_sessions[session_id]

                # Persist the source mime type for diagnostics
                if not session.get("source_mime_type"):
                    session["source_mime_type"] = mime_type

                # If source is WebM, buffer container bytes and defer decode until batch time
                if session["source_mime_type"] and "webm" in session["source_mime_type"].lower():
                    session["webm_buffer"].extend(audio_bytes)
                    decoded_len = 0
                else:
                    # Decode to target PCM and append to the running buffer (WAV or unknown path)
                    try:
                        pcm_bytes = self._decode_to_pcm(audio_bytes, mime_type)
                        decoded_len = len(pcm_bytes)
                    except Exception as decode_error:
                        self.logger.warning(f"PCM decode failed for chunk {sequence_number}: {decode_error}")
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": f"PCM decode failed for chunk {sequence_number}: {decode_error}",
                            "timestamp": datetime.now().isoformat()
                        }))
                        return

                if not (session["source_mime_type"] and "webm" in session["source_mime_type"].lower()):
                    session["pcm_buffer"].extend(pcm_bytes)
                    session["full_pcm_buffer"].extend(pcm_bytes)

                # Store only metadata for acknowledgments and counting
                session["chunks"].append({
                    "timestamp": timestamp,
                    "sequence_number": sequence_number,
                    "mime_type": mime_type,
                    "decoded_pcm_bytes": decoded_len,
                })
                session["total_chunks"] += 1

                # Send acknowledgment
                await websocket.send_text(json.dumps({
                    "type": "audio_ack",
                    "sequenceNumber": sequence_number,
                    "timestamp": timestamp,
                    "message": "Audio chunk received",
                    "processed_at": datetime.now().isoformat(),
                    "batch_size": len(session["chunks"])
                }))

                # Check if we should process a batch
                should_process = (
                    len(session["chunks"]) >= self.MIN_CHUNKS_FOR_BATCH or  # Minimum chunks reached
                    len(session["chunks"]) >= self.MAX_CHUNKS_FOR_BATCH or  # Maximum chunks reached
                    (datetime.now() - session["last_processed"]).seconds >= self.BATCH_SIZE_SECONDS  # Time threshold
                )

                if should_process:
                    await self.process_audio_batch(session_id)

        except Exception as e:
            self.logger.error(f"Error processing audio chunk: {e}")
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": f"Failed to process audio chunk: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }))

    async def process_audio_batch(self, session_id: str):
        """Process a batch of audio chunks"""
        if session_id not in self.audio_sessions:
            return

        session = self.audio_sessions[session_id]
        chunks = session["chunks"]

        if not chunks:
            return

        try:
            self.logger.info(f"Processing batch for session {session_id}: {len(chunks)} chunks")

            source_mime = (session.get("source_mime_type") or "").lower()
            if "webm" in source_mime:
                # Decode entire WebM buffer to PCM, then take the new slice since last batch
                webm_bytes = bytes(session["webm_buffer"])
                try:
                    pcm_full = self._decode_to_pcm(webm_bytes, "webm")
                except Exception as e:
                    self.logger.warning(f"Batch WebM decode failed: {e}")
                    await session["websocket"].send_text(json.dumps({
                        "type": "error",
                        "message": f"Batch WebM decode failed: {e}",
                        "timestamp": datetime.now().isoformat()
                    }))
                    return

                start_pcm = session.get("processed_pcm_offset", 0)
                if len(pcm_full) <= start_pcm:
                    self.logger.debug("No new PCM produced from WebM for this batch")
                    return

                pcm_slice = pcm_full[start_pcm:]
                wav_bytes = self._wav_from_pcm(pcm_slice)
                session["processed_pcm_offset"] = len(pcm_full)

                total_size = len(wav_bytes)
                self.logger.debug(f"Built WAV from WebM PCM slice: {total_size} bytes (pcm {len(pcm_slice)}), source={source_mime}")
                self.logger.debug(f"WAV header preview: {wav_bytes[:20].hex()}")
            else:
                # Build WAV from the newly added PCM slice
                pcm_buffer: bytearray = session["pcm_buffer"]
                start_offset: int = session.get("last_batch_offset", 0)
                end_offset: int = len(pcm_buffer)

                if end_offset <= start_offset:
                    self.logger.debug("No new PCM to process for this batch")
                    return

                pcm_slice = bytes(pcm_buffer[start_offset:end_offset])
                wav_bytes = self._wav_from_pcm(pcm_slice)

                total_size = len(wav_bytes)

                self.logger.debug(f"Built WAV from PCM slice: {total_size} bytes (pcm {len(pcm_slice)}), source={session.get('source_mime_type')}")
                self.logger.debug(f"WAV header preview: {wav_bytes[:20].hex()}")

            # Send batch processing status
            await session["websocket"].send_text(json.dumps({
                "type": "batch_processing",
                "message": f"Processing batch of {len(chunks)} chunks ({total_size} bytes)",
                "timestamp": datetime.now().isoformat()
            }))

            # Process the WAV bytes for this batch
            session_language = session.get("language", "en")
            self.logger.debug(f"Processing batch for session {session_id} with language: {session_language}")
            transcription_result = await self.batch_transcribe_audio(wav_bytes, session_id, len(chunks), session_language)

            # Send transcription result
            await session["websocket"].send_text(json.dumps({
                "type": "batch_transcription",
                "text": transcription_result["text"],
                "confidence": transcription_result["confidence"],
                "chunk_count": len(chunks),
                "duration_seconds": transcription_result["duration"],
                "timestamp": datetime.now().isoformat(),
                "ready_for_llm": True  # Flag indicating this is ready for LLM processing
            }))

            # Advance offsets and optionally compact buffers
            if "webm" in source_mime:
                # Keep the cumulative webm_buffer; optional future compaction could preserve only key headers + tail
                pass
            else:
                session["last_batch_offset"] = end_offset
                # Compact buffer: drop processed PCM and reset offset
                del pcm_buffer[:end_offset]
                session["last_batch_offset"] = 0

            # Clear processed chunk metadata
            session["chunks"] = []
            session["last_processed"] = datetime.now()

            self.logger.info(f"Batch processing complete for session {session_id}")

        except Exception as e:
            self.logger.error(f"Error processing batch: {e}")
            await session["websocket"].send_text(json.dumps({
                "type": "error",
                "message": f"Batch processing failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }))

    async def process_final_batch(self, session_id: str):
        """Process any remaining chunks when recording ends"""
        if session_id not in self.audio_sessions:
            return

        session = self.audio_sessions[session_id]

        if session["chunks"]:
            await self.process_audio_batch(session_id)

        websocket = session.get("websocket")
        if websocket and websocket.application_state == WebSocketState.CONNECTED:
            try:
                await websocket.send_text(json.dumps({
                    "type": "recording_complete",
                    "message": "Recording session completed",
                    "total_chunks_processed": session["total_chunks"],
                    "timestamp": datetime.now().isoformat()
                }))
            except Exception as exc:
                self.logger.warning(f"Failed to send recording_complete message for session {session_id}: {exc}")

        # Close the websocket to force a fresh session on next recording
        if websocket and websocket.client_state == WebSocketState.CONNECTED:
            try:
                await websocket.close()
            except Exception:
                pass

    async def finalize_session_recording(self, session_id: str):
        """Persist the complete session audio to Azure blob storage."""
        session = self.audio_sessions.get(session_id)
        if not session:
            return

        if session.get("finalized"):
            return

        try:
            wav_bytes = await self._build_full_wav(session)
            if not wav_bytes:
                self.logger.info(f"No audio captured for session {session_id}; skipping upload")
                return

            metadata = {
                "language": session.get("language", "unknown"),
                "source_mime": session.get("source_mime_type") or "unknown",
                "total_chunks": str(session.get("total_chunks", 0)),
                "started_at": session.get("start_time").isoformat() if session.get("start_time") else "",
            }

            blob_name = await azure_blob_service.upload_session_audio(
                session_id=session_id,
                wav_bytes=wav_bytes,
                language=session.get("language"),
                metadata=metadata,
            )

            if blob_name:
                self.logger.info(f"Session {session_id} recording uploaded to {blob_name}")
            session["finalized"] = True
        except Exception as exc:
            self.logger.error(f"Failed to upload session {session_id} recording: {exc}")

    async def _build_full_wav(self, session: Dict[str, Any]) -> Optional[bytes]:
        source_mime = (session.get("source_mime_type") or "").lower()

        if "webm" in source_mime:
            if not session.get("webm_buffer"):
                return None
            try:
                pcm_bytes = self._decode_to_pcm(bytes(session["webm_buffer"]), "webm")
            except Exception as exc:
                self.logger.warning(f"Failed to decode WebM buffer for full session: {exc}")
                return None
        else:
            pcm_bytes = bytes(session.get("full_pcm_buffer") or b"")

        if not pcm_bytes:
            return None

        return self._wav_from_pcm(pcm_bytes)

    async def handle_other_messages(self, websocket: WebSocket, message: Dict[str, Any]):
        """Handle other types of WebSocket messages"""
        message_type = message.get("type")

        if message_type == "ping":
            await websocket.send_text(json.dumps({
                "type": "pong",
                "timestamp": datetime.now().isoformat()
            }))
        elif message_type == "start_recording":
            await websocket.send_text(json.dumps({
                "type": "recording_started",
                "message": "Recording session started",
                "timestamp": datetime.now().isoformat()
            }))
        elif message_type == "stop_recording":
            await websocket.send_text(json.dumps({
                "type": "recording_stopped",
                "message": "Recording session stopped",
                "timestamp": datetime.now().isoformat()
            }))
        else:
            await websocket.send_text(json.dumps({
                "type": "unknown_message",
                "message": f"Unknown message type: {message_type}",
                "timestamp": datetime.now().isoformat()
            }))

    async def batch_transcribe_audio(self, audio_bytes: bytes, session_id: str, chunk_count: int, language: str = "en") -> Dict[str, Any]:
        """Transcribe combined audio using OpenAI Whisper API"""
        # Import here to avoid circular imports
        from .transcription_service import TranscriptionService

        transcription_service = TranscriptionService()
        return await transcription_service.transcribe_audio(audio_bytes, session_id, chunk_count, language)


# Global instance
audio_service = AudioProcessingService()
