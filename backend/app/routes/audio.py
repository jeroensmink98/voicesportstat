from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..services.audio_service import audio_service

router = APIRouter()


@router.websocket("/ws/audio")
async def websocket_audio_endpoint(websocket: WebSocket):
    """WebSocket endpoint for receiving audio chunks from the frontend"""
    await audio_service.handle_websocket_connection(websocket)
