#!/usr/bin/env python3
"""
Test script for audio conversion functionality
"""
import asyncio
import tempfile
from pathlib import Path
from main import convert_audio_to_wav

async def test_audio_conversion():
    """Test the audio conversion function"""
    print("Testing audio conversion...")
    
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create a dummy WAV file (just some bytes)
        input_file = temp_path / "test_input.wav"
        output_file = temp_path / "test_output.wav"

        # Write some dummy data
        with open(input_file, "wb") as f:
            f.write(b"dummy wav data" * 100)  # Some dummy data
        
        print(f"Created test input file: {input_file}")
        print(f"File size: {input_file.stat().st_size} bytes")
        
        # Test conversion
        success = await convert_audio_to_wav(input_file, output_file)
        
        if success:
            print(f"✅ Audio conversion successful!")
            print(f"Output file: {output_file}")
            print(f"Output file size: {output_file.stat().st_size} bytes")
        else:
            print("❌ Audio conversion failed")
            print("Make sure ffmpeg is installed and available in PATH")

if __name__ == "__main__":
    asyncio.run(test_audio_conversion())
