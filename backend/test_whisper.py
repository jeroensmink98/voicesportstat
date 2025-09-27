#!/usr/bin/env python3
"""
Test script to verify OpenAI Whisper integration
"""

import os
import asyncio
from dotenv import load_dotenv
import openai

# Load environment variables
load_dotenv()

def test_openai_connection():
    """Test OpenAI API connection"""
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment variables")
        print("Please create a .env file with your OpenAI API key")
        return False
    
    if not api_key.startswith("sk-"):
        print("❌ Invalid API key format (should start with 'sk-')")
        return False
    
    try:
        client = openai.OpenAI(api_key=api_key)
        
        # Test with a simple API call (list models)
        models = client.models.list()
        print("✅ OpenAI API connection successful")
        print(f"✅ Found {len(models.data)} available models")
        
        # Check if whisper-1 is available
        whisper_available = any(model.id == "whisper-1" for model in models.data)
        if whisper_available:
            print("✅ whisper-1 model is available")
        else:
            print("⚠️ whisper-1 model not found in available models")
        
        return True
        
    except Exception as e:
        print(f"❌ OpenAI API connection failed: {e}")
        return False

def test_environment_setup():
    """Test environment setup"""
    print("🔍 Testing environment setup...")
    
    # Check if .env file exists
    if os.path.exists(".env"):
        print("✅ .env file found")
    else:
        print("❌ .env file not found")
        print("Please create a .env file with OPENAI_API_KEY=sk-your-key-here")
        return False
    
    return test_openai_connection()

if __name__ == "__main__":
    print("🧪 Testing OpenAI Whisper Integration")
    print("=" * 40)
    
    success = test_environment_setup()
    
    if success:
        print("\n🎉 Setup is ready!")
        print("You can now run: uv run fastapi dev")
    else:
        print("\n❌ Setup incomplete")
        print("Please check the errors above and fix them")


