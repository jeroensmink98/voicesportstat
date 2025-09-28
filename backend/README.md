# VoiceSportStat Backend

FastAPI backend for handling audio streaming and transcription via WebSocket.

## Setup

1. **Install dependencies**:
   ```bash
   cd backend
   uv sync
   ```

2. **Configure environment variables**:
   Create a `.env` file with your OpenAI API key and Azure storage credentials:
   ```bash
   OPENAI_API_KEY=sk-your-openai-api-key-here
   AZURE_STORAGE_ACCOUNT_NAME=your-account-name
   AZURE_STORAGE_ACCOUNT_KEY=your-account-key
   AZURE_STORAGE_CONTAINER=recordings  # optional override
   ```

3. **Run the server**:
   ```bash
   uv run fastapi dev
   ```
   
   Or with the custom script:
   ```bash
   python run_server.py
   ```

## API Endpoints

- `GET /` - Health check
- `GET /health` - Detailed health status
- `GET /transcriptions` - List all transcription files
- `GET /transcriptions/{filename}` - Get specific transcription file
- `WS /ws/audio` - WebSocket endpoint for audio streaming

## WebSocket Protocol

The `/ws/audio` endpoint handles real-time audio streaming:

### Client → Server Messages

```json
{
  "type": "audio_chunk",
  "data": [/* audio bytes array */],
  "timestamp": 1640995200000,
  "sequenceNumber": 1,
  "mimeType": "audio/wav"
}
```

### Server → Client Messages

**Connection confirmation**:
```json
{
  "type": "connection",
  "message": "WebSocket connected successfully",
  "timestamp": "2024-01-01T12:00:00"
}
```

**Audio acknowledgment**:
```json
{
  "type": "audio_ack",
  "sequenceNumber": 1,
  "timestamp": 1640995200000,
  "message": "Audio chunk received and processed",
  "processed_at": "2024-01-01T12:00:00"
}
```

**Transcription result**:
```json
{
  "type": "transcription",
  "sequenceNumber": 10,
  "timestamp": 1640995200000,
  "text": "Hello, this is a test recording.",
  "confidence": 0.85,
  "processed_at": "2024-01-01T12:00:00"
}
```

## Features

- ✅ Real-time audio streaming via WebSocket
- ✅ Audio chunk acknowledgment
- ✅ OpenAI Whisper API integration
- ✅ Batch processing for optimal accuracy
- ✅ JSON file output for transcriptions
- ✅ Automatic upload of complete session recordings to Azure Blob Storage with metadata
- ✅ Error handling and connection management
- ✅ CORS support for frontend integration
- ✅ Transcription file management API

## Transcription Files

Transcriptions are automatically saved to the `transcriptions/` directory as JSON files with the format:

```json
{
  "session_id": "session_20240101_120000_12345",
  "timestamp": "2024-01-01T12:00:00",
  "transcription": {
    "text": "Welcome to the sports statistics recording session...",
    "confidence": 0.95,
    "duration_seconds": 5.25,
    "chunk_count": 21,
    "audio_size_bytes": 125000
  },
  "metadata": {
    "model": "whisper-1",
    "language": "en",
    "processing_timestamp": "2024-01-01T12:00:05",
    "ready_for_llm": true
  }
}
```

## Usage Examples

### List all transcriptions:
```bash
curl http://localhost:8000/transcriptions
```

### Get a specific transcription:
```bash
curl http://localhost:8000/transcriptions/transcription_session_20240101_120000_12345_20240101_120005.json
```

## Cost Information

- OpenAI Whisper API: $0.006 per minute of audio
- Batch processing reduces API calls by ~80%
- Typical session costs: $0.01-0.10 per recording