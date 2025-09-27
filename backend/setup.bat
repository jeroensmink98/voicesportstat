@echo off
echo 🚀 Setting up VoiceSportStat Backend with OpenAI Whisper
echo ==================================================

REM Check if .env file exists
if not exist ".env" (
    echo ❌ .env file not found
    echo Creating .env file template...
    echo OPENAI_API_KEY=sk-your-openai-api-key-here > .env
    echo ✅ Created .env file template
    echo 📝 Please edit .env file and add your OpenAI API key
    echo    Get your API key from: https://platform.openai.com/api-keys
    pause
    exit /b 1
)

REM Install dependencies
echo 📦 Installing dependencies...
uv sync

REM Test the setup
echo 🧪 Testing OpenAI connection...
python test_whisper.py

if %errorlevel% equ 0 (
    echo.
    echo 🎉 Setup complete!
    echo.
    echo To start the server:
    echo   uv run fastapi dev
    echo.
    echo To test transcription:
    echo   1. Start the frontend: cd ../client ^&^& pnpm dev
    echo   2. Start recording in the browser
    echo   3. Check transcriptions: curl http://localhost:8000/transcriptions
) else (
    echo.
    echo ❌ Setup failed. Please check the errors above.
)

pause
