# Environment Setup for OpenAI Whisper Integration

## Required Environment Variables

Create a `.env` file in the `backend/` directory with the following content:

```bash
# OpenAI API Configuration
OPENAI_API_KEY=sk-your-openai-api-key-here
```

## Getting Your OpenAI API Key

1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign in or create an account
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key (starts with `sk-`)
6. Add it to your `.env` file

## Installation

### 1. Install Python Dependencies

After setting up your `.env` file, install the new dependencies:

```bash
cd backend
uv sync
```

### 2. Install FFmpeg (Required for Audio Conversion)

The backend uses FFmpeg for audio format conversion when needed. The application now primarily processes WAV audio files directly.

#### Windows
```bash
# Option 1: Using winget (recommended)
winget install ffmpeg

# Option 2: Download from https://ffmpeg.org/download.html
# Extract and add to PATH
```

#### macOS
```bash
# Using Homebrew
brew install ffmpeg
```

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install ffmpeg
```

#### Verify Installation
```bash
ffmpeg -version
```

You should see FFmpeg version information if installed correctly.

## Testing the Setup

1. Start the backend server:
   ```bash
   uv run fastapi dev
   ```

2. Test the transcription endpoints:
   - List transcriptions: `GET http://localhost:8000/transcriptions`
   - Get specific transcription: `GET http://localhost:8000/transcriptions/{filename}`

## Security Notes

- Never commit your `.env` file to version control
- Keep your API key secure and don't share it
- The `.env` file is already in `.gitignore`

## Cost Information

OpenAI Whisper API pricing:
- $0.006 per minute of audio
- Very cost-effective for batch processing approach

Example costs for typical usage:
- 1 minute recording: $0.006
- 10 minute recording: $0.06
- 1 hour recording: $0.36
