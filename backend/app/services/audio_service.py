import json
import asyncio
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path
import wave
import io

from fastapi import WebSocket, WebSocketDisconnect

from ..models.audio import (
    AudioChunk, AudioSession, WebSocketMessage,
    TranscriptionResult, TranscriptionResponse, RecordingCompleteInfo
)


class AudioProcessingService:
    """Service for handling audio processing, WebSocket connections, and batch processing"""

    def __init__(self):
        # Global storage for audio sessions
        self.audio_sessions: Dict[str, Dict[str, Any]] = {}

        # Batch processing configuration
        self.BATCH_SIZE_SECONDS = 5  # Process every 5 seconds of audio
        self.MIN_CHUNKS_FOR_BATCH = 5   # Minimum chunks before processing
        self.MAX_CHUNKS_FOR_BATCH = 20  # Maximum chunks before forcing processing

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
                "websocket": websocket
            }

            # Send welcome message
            await websocket.send_text(json.dumps({
                "type": "connection",
                "message": "WebSocket connected successfully",
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }))

            print(f"WebSocket connection established for session {session_id} at {datetime.now()}")

            while True:
                try:
                    # Receive audio chunk data from frontend
                    data = await websocket.receive_text()
                    message = json.loads(data)

                    if message.get("type") == "audio_chunk":
                        # Process audio chunk with batch logic
                        await self.process_audio_chunk_batch(websocket, session_id, message)
                    elif message.get("type") == "end_recording":
                        # Process final batch
                        await self.process_final_batch(session_id)
                        break
                    else:
                        # Handle other message types
                        await self.handle_other_messages(websocket, message)

                except WebSocketDisconnect:
                    print(f"WebSocket disconnected for session {session_id} at {datetime.now()}")
                    break
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}")
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Invalid JSON format",
                        "timestamp": datetime.now().isoformat()
                    }))
                except Exception as e:
                    print(f"Error processing message: {e}")
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": f"Server error: {str(e)}",
                        "timestamp": datetime.now().isoformat()
                    }))

        except WebSocketDisconnect:
            print(f"WebSocket connection closed for session {session_id} at {datetime.now()}")
        except Exception as e:
            print(f"WebSocket error: {e}")
        finally:
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
            mime_type = message.get("mimeType", "audio/webm")

            # Convert bytes array back to bytes
            audio_bytes = bytes(audio_data)

            print(f"Session {session_id} - Received chunk {sequence_number}: {len(audio_bytes)} bytes")

            # Add chunk to session
            if session_id in self.audio_sessions:
                session = self.audio_sessions[session_id]
                session["chunks"].append({
                    "data": audio_bytes,
                    "timestamp": timestamp,
                    "sequence_number": sequence_number,
                    "mime_type": mime_type
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
            print(f"Error processing audio chunk: {e}")
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
            print(f"Processing batch for session {session_id}: {len(chunks)} chunks")

            # Combine all audio chunks into a single buffer
            combined_audio_chunks = []
            total_size = 0

            for chunk in chunks:
                combined_audio_chunks.append(chunk["data"])
                total_size += len(chunk["data"])

            # Concatenate all chunks
            combined_audio = b''.join(combined_audio_chunks)

            print(f"Combined audio size: {len(combined_audio)} bytes from {len(chunks)} chunks")
            print(f"Total audio duration estimate: {len(chunks) * 0.25} seconds")

            # Debug: Check if we have valid WebM data
            print(f"First 20 bytes: {combined_audio[:20].hex()}")
            if len(combined_audio) > 20:
                print(f"Last 20 bytes: {combined_audio[-20:].hex()}")

            # Send batch processing status
            await session["websocket"].send_text(json.dumps({
                "type": "batch_processing",
                "message": f"Processing batch of {len(chunks)} chunks ({total_size} bytes)",
                "timestamp": datetime.now().isoformat()
            }))

            # Process the combined audio
            transcription_result = await self.batch_transcribe_audio(combined_audio, session_id, len(chunks))

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

            # Clear processed chunks
            session["chunks"] = []
            session["last_processed"] = datetime.now()

            print(f"Batch processing complete for session {session_id}")

        except Exception as e:
            print(f"Error processing batch: {e}")
            await session["websocket"].send_text(json.dumps({
                "type": "error",
                "message": f"Batch processing failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }))

    async def process_final_batch(self, session_id: str):
        """Process any remaining chunks when recording ends"""
        if session_id in self.audio_sessions and self.audio_sessions[session_id]["chunks"]:
            await self.process_audio_batch(session_id)

            # Send final summary
            session = self.audio_sessions[session_id]
            await session["websocket"].send_text(json.dumps({
                "type": "recording_complete",
                "message": "Recording session completed",
                "total_chunks_processed": session["total_chunks"],
                "timestamp": datetime.now().isoformat()
            }))

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

    async def batch_transcribe_audio(self, audio_bytes: bytes, session_id: str, chunk_count: int) -> Dict[str, Any]:
        """Transcribe combined audio using OpenAI Whisper API"""
        # Import here to avoid circular imports
        from .transcription_service import TranscriptionService

        transcription_service = TranscriptionService()
        return await transcription_service.transcribe_audio(audio_bytes, session_id, chunk_count)


# Global instance
audio_service = AudioProcessingService()
