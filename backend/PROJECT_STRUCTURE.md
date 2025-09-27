# VoiceSportStat Backend - Project Structure & Setup Guide

## 📋 Overview

VoiceSportStat is a FastAPI-based backend application that provides real-time audio transcription services using OpenAI's Whisper API. The application receives audio chunks via WebSocket (usually WebM/Opus or WAV depending on browser support), decodes them to PCM, aggregates PCM per session, and transcribes batch slices as valid WAV.

## 🏗️ Architecture & Structure

### Before Refactoring
- Single monolithic `main.py` file (773 lines)
- All logic mixed together (WebSocket handling, audio processing, transcription, file management)
- Difficult to test and maintain

### After Refactoring (Current Structure)
Following FastAPI best practices with proper separation of concerns:

```
backend/
├── app/                          # Main application package
│   ├── __init__.py
│   ├── config.py                 # Configuration and constants
│   ├── models/                   # Pydantic models
│   │   ├── __init__.py
│   │   ├── audio.py             # Audio-related models
│   │   └── responses.py         # API response models
│   ├── routes/                   # HTTP and WebSocket endpoints
│   │   ├── __init__.py
│   │   ├── audio.py             # WebSocket audio endpoint
│   │   ├── health.py            # Health check endpoints
│   │   └── transcriptions.py    # Transcription file endpoints
│   └── services/                 # Business logic
│       ├── __init__.py
│       ├── audio_service.py     # WebSocket and batch processing
│       ├── transcription_service.py  # OpenAI Whisper integration
│       ├── file_conversion_service.py  # Audio format conversion
│       └── file_service.py      # File management operations
├── main.py                      # Application entrypoint (40 lines)
├── pyproject.toml               # Dependencies and project config
├── uv.lock                      # Dependency lock file
└── transcriptions/              # Generated transcription files
```

## 🔧 Setup & Dependencies

### Prerequisites
- Python 3.10+
- `uv` package manager
- FFmpeg (for audio conversion)
- OpenAI API key

### Installation
```bash
# Install dependencies
uv sync

# Set up environment variables
cp .env.example .env  # Add your OPENAI_API_KEY
```

### Environment Variables
```env
OPENAI_API_KEY=your_openai_api_key_here
```

## 🚀 Running the Application

### Development Server
```bash
# From backend directory
uv run fastapi dev

# Or run directly with Python
uv run python main.py
```

The server will start on `http://localhost:8000`

### Production Deployment
```bash
# Using uvicorn directly
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

## 📡 API Endpoints

### Health Endpoints
- `GET /` - Root endpoint with basic info
- `GET /health` - Health check

### Transcription Management
- `GET /transcriptions` - List all transcription files
- `GET /transcriptions/{filename}` - Get specific transcription file

### WebSocket Audio Streaming
- `WebSocket /ws/audio` - Real-time audio chunk processing (PCM aggregation, WAV-per-batch to Whisper)

## 🔄 WebSocket Message Flow

### Client → Server Messages
```json
{
  "type": "audio_chunk",
  "data": [/* base64 audio bytes */],
  "timestamp": "2024-01-01T00:00:00Z",
  "sequenceNumber": 1,
  "mimeType": "audio/wav"
}
```

### Server → Client Messages
```json
{
  "type": "audio_ack",
  "sequenceNumber": 1,
  "message": "Audio chunk received"
}
```

```json
{
  "type": "batch_transcription",
  "text": "Transcribed text...",
  "confidence": 0.95,
  "chunk_count": 5,
  "duration_seconds": 5.0,
  "ready_for_llm": true
}
```

## 🏛️ Architecture Patterns

### Service Layer Pattern
Each service handles a specific domain:
- **AudioProcessingService**: WebSocket connections and batch processing
- **TranscriptionService**: OpenAI Whisper API integration
- **FileConversionService**: Audio format conversion (WebM → WAV/MP3)
- **FileManagementService**: Transcription file operations

### Repository Pattern Ready
The structure is prepared for database integration with repository services.

### Dependency Injection
Services are instantiated as singletons and imported where needed.

## 🧪 Testing

### Running Tests
```bash
# Install test dependencies if needed
uv add pytest pytest-asyncio

# Run tests
uv run pytest
```

### Manual Testing
1. Start the server: `uv run fastapi dev`
2. Test health endpoint: `curl http://localhost:8000/health`
3. Test WebSocket with a client that can send audio chunks

## 🔒 Security Considerations

- CORS is configured for development (localhost origins)
- OpenAI API key should be in environment variables, not code
- Consider rate limiting for production
- WebSocket connections should be validated

## 📊 Monitoring & Logging

### Current Logging
- Console logging for debugging
- File operations logged to stdout
- WebSocket events logged

### Production Monitoring
Consider adding:
- Structured logging (JSON format)
- Metrics collection (Prometheus)
- Health check endpoints
- Request/response logging middleware

## 🔄 Data Flow

1. **Audio Reception**: Frontend sends audio chunks via WebSocket (WebM/Opus or WAV)
2. **PCM Aggregation**: Server decodes to PCM S16LE 16k mono and aggregates
3. **Batch WAV Build**: For each batch, a fresh WAV is built from new PCM slice
4. **Transcription**: OpenAI Whisper API processes each batch WAV to text
5. **Storage**: Results saved as JSON files in `transcriptions/` directory
6. **Response**: Transcription results sent back to frontend

## 🛠️ Development Workflow

### Adding New Features
1. Add models in `app/models/`
2. Create/update services in `app/services/`
3. Add routes in `app/routes/`
4. Update `main.py` if needed
5. Add tests

### Code Style
- Follow PEP 8 for Python code
- Use type hints
- Add docstrings for public methods
- Keep services focused and testable

## 📈 Performance Considerations

### Current Optimizations
- Batch processing reduces API calls
- Temporary file cleanup prevents disk space issues
- WebSocket connection management
- **Updated**: Now processes WAV audio chunks directly (no conversion needed)

### Potential Improvements
- Audio compression before processing
- Caching for repeated requests
- Async file operations
- Connection pooling for OpenAI API

## 🔧 Configuration

All configuration is centralized in `app/config.py`:
- API settings
- Batch processing parameters
- File paths
- CORS origins

## 📝 File Structure Details

### `main.py` (40 lines)
Minimal entrypoint that:
- Imports FastAPI and middleware
- Includes routers with prefixes
- Runs the application

### `app/config.py`
Centralized configuration:
- OpenAI API settings
- CORS configuration
- Batch processing parameters
- File system paths

### `app/models/`
Pydantic models for:
- Audio chunk validation
- WebSocket message structures
- API responses
- Transcription data

### `app/routes/`
HTTP and WebSocket endpoints:
- Health checks (`/`, `/health`)
- Transcription management (`/transcriptions/*`)
- Audio streaming (`/ws/audio`)

### `app/services/`
Business logic services:
- `AudioProcessingService`: WebSocket and batch processing
- `TranscriptionService`: OpenAI Whisper integration
- `FileConversionService`: Audio format conversion
- `FileManagementService`: File operations

## 🎯 Next Steps & Roadmap

### Immediate
- Add comprehensive error handling
- Implement proper logging
- Add request validation middleware
- Create API documentation (OpenAPI/Swagger)

### Future
- Database integration for transcriptions
- User authentication and authorization
- Real-time collaboration features
- Audio quality analysis
- Export functionality (PDF, DOCX)
- Admin dashboard

## 🤝 Contributing

When contributing to this project:
1. Follow the established structure
2. Add tests for new features
3. Update documentation
4. Use meaningful commit messages
5. Consider backward compatibility

## 📞 Support

For issues or questions:
- Check existing documentation
- Review the refactor plan in `restructure-plan.md`
- Examine the transcription strategy in `TRANSCRIPTION_STRATEGY.md`
- Check environment setup in `ENVIRONMENT_SETUP.md`
