import os
import shutil
from pathlib import Path
from typing import List

import ffmpeg


class FileConversionService:
    """Service for converting audio files between different formats"""

    async def convert_webm_to_wav(self, input_path: Path, output_path: Path) -> bool:
        """Convert WebM file to WAV format using ffmpeg"""
        try:
            # Check if ffmpeg is available
            if not shutil.which("ffmpeg"):
                print("ERROR: ffmpeg not found")
                return False

            # Check file size first
            file_size = input_path.stat().st_size
            if file_size < 100:
                print(f"ERROR: WebM file too small ({file_size} bytes)")
                return False

            print(f"Converting WebM to WAV: {input_path} -> {output_path} (size: {file_size} bytes)")

            # Try multiple conversion approaches
            conversion_attempts = [
                # Method 1: Standard conversion
                {
                    "name": "Standard conversion",
                    "stream": ffmpeg.input(str(input_path)).output(
                        str(output_path),
                        acodec='pcm_s16le',
                        ar=16000,
                        ac=1
                    ).overwrite_output()
                },
                # Method 2: Force format detection
                {
                    "name": "Force format",
                    "stream": ffmpeg.input(str(input_path), f='webm').output(
                        str(output_path),
                        acodec='pcm_s16le',
                        ar=16000,
                        ac=1
                    ).overwrite_output()
                }
            ]

            for attempt in conversion_attempts:
                try:
                    print(f"Trying {attempt['name']}...")
                    ffmpeg.run(attempt["stream"], capture_stdout=True, capture_stderr=True)

                    # Check if output file was created and has content
                    if output_path.exists() and output_path.stat().st_size > 0:
                        file_size = output_path.stat().st_size
                        print(f"✓ {attempt['name']} successful: {output_path} ({file_size} bytes)")
                        return True
                    else:
                        print(f"✗ {attempt['name']} failed - no output file")

                except ffmpeg.Error as e:
                    print(f"✗ {attempt['name']} ffmpeg error: {e.stderr.decode('utf-8')[:200]}...")
                except Exception as e:
                    print(f"✗ {attempt['name']} exception: {e}")

            print("All WAV conversion methods failed")
            return False

        except Exception as e:
            print(f"ERROR: Exception during WebM to WAV conversion: {e}")
            return False

    async def convert_webm_to_mp3(self, input_path: Path, output_path: Path) -> bool:
        """Convert WebM file to MP3 format using ffmpeg"""
        try:
            # Check if ffmpeg is available
            if not shutil.which("ffmpeg"):
                print("ERROR: ffmpeg not found")
                return False

            # Check file size first
            file_size = input_path.stat().st_size
            if file_size < 100:
                print(f"ERROR: WebM file too small ({file_size} bytes)")
                return False

            print(f"Converting WebM to MP3: {input_path} -> {output_path} (size: {file_size} bytes)")

            # Convert to MP3
            stream = ffmpeg.input(str(input_path)).output(
                str(output_path),
                acodec='libmp3lame',
                ar=16000,
                ac=1,
                ab='128k'
            ).overwrite_output()

            ffmpeg.run(stream, capture_stdout=True, capture_stderr=True)

            # Check if output file was created and has content
            if output_path.exists() and output_path.stat().st_size > 0:
                file_size = output_path.stat().st_size
                print(f"✓ MP3 conversion successful: {output_path} ({file_size} bytes)")
                return True
            else:
                print("✗ MP3 conversion failed - no output file")
                return False

        except Exception as e:
            print(f"ERROR: Exception during WebM to MP3 conversion: {e}")
            return False

    async def validate_webm_file(self, file_path: Path) -> bool:
        """Validate that a WebM file is properly formatted and not corrupted"""
        try:
            if not file_path.exists():
                print(f"File does not exist: {file_path}")
                return False

            file_size = file_path.stat().st_size
            if file_size < 100:
                print(f"File too small ({file_size} bytes): {file_path}")
                return False

            # Try to read the file header to check if it's a valid WebM file
            with open(file_path, "rb") as f:
                header = f.read(8)
                # WebM files start with specific bytes
                if header.startswith(b'\x1a\x45\xdf\xa3'):  # WebM/Matroska header
                    print(f"Valid WebM header detected: {file_path}")
                    return True
                else:
                    print(f"Invalid WebM header: {file_path} (first 8 bytes: {header.hex()})")
                    return False

        except Exception as e:
            print(f"Error validating WebM file {file_path}: {e}")
            return False

    async def convert_audio_to_wav(self, input_path: Path, output_path: Path) -> bool:
        """Convert audio file to WAV format using ffmpeg-python"""
        try:
            # Check if ffmpeg is available
            if not shutil.which("ffmpeg"):
                print("ERROR: ffmpeg not found. Please install ffmpeg to convert audio files.")
                print("Installation instructions:")
                print("  Windows: Download from https://ffmpeg.org/download.html or use 'winget install ffmpeg'")
                print("  macOS: 'brew install ffmpeg'")
                print("  Ubuntu/Debian: 'sudo apt install ffmpeg'")
                return False

            # Check file size first - if it's too small, it might be corrupted
            file_size = input_path.stat().st_size
            if file_size < 100:  # Less than 100 bytes is likely corrupted
                print(f"ERROR: Audio file too small ({file_size} bytes), likely corrupted")
                return False

            print(f"Converting audio: {input_path} -> {output_path} (size: {file_size} bytes)")

            # Try different approaches for WebM conversion using ffmpeg-python
            conversion_attempts = [
                # Method 1: Auto-detect with WebM container format
                {
                    "name": "Auto-detect with WebM container",
                    "stream": ffmpeg
                        .input(str(input_path), f='webm')
                        .output(
                            str(output_path),
                            acodec='pcm_s16le',
                            ar=16000,
                            ac=1,
                            f='wav'
                        )
                        .overwrite_output()
                },
                # Method 2: Try with matroska container (WebM is a subset of Matroska)
                {
                    "name": "Matroska container",
                    "stream": ffmpeg
                        .input(str(input_path), f='matroska')
                        .output(
                            str(output_path),
                            acodec='pcm_s16le',
                            ar=16000,
                            ac=1,
                            f='wav'
                        )
                        .overwrite_output()
                },
                # Method 3: Try without specifying input format (let ffmpeg auto-detect)
                {
                    "name": "Auto-detect input format",
                    "stream": ffmpeg
                        .input(str(input_path))
                        .output(
                            str(output_path),
                            acodec='pcm_s16le',
                            ar=16000,
                            ac=1,
                            f='wav'
                        )
                        .overwrite_output()
                },
                # Method 4: Try with different audio codec detection
                {
                    "name": "WebM with opus codec",
                    "stream": ffmpeg
                        .input(str(input_path), f='webm', acodec='libopus')
                        .output(
                            str(output_path),
                            acodec='pcm_s16le',
                            ar=16000,
                            ac=1,
                            f='wav'
                        )
                        .overwrite_output()
                }
            ]

            for attempt in conversion_attempts:
                print(f"Trying {attempt['name']}...")
                try:
                    # Run the ffmpeg conversion
                    ffmpeg.run(attempt["stream"], capture_stdout=True, capture_stderr=True, timeout=30)

                    # Check if output file was created and has content
                    if output_path.exists() and output_path.stat().st_size > 0:
                        file_size = output_path.stat().st_size
                        print(f"✓ {attempt['name']} successful: {output_path} ({file_size} bytes)")
                        return True
                    else:
                        print(f"✗ {attempt['name']} failed - no output file created")

                except ffmpeg.Error as e:
                    print(f"✗ {attempt['name']} failed with ffmpeg error")
                    if e.stderr:
                        print(f"  Error: {e.stderr.decode('utf-8')[:200]}...")
                except Exception as e:
                    print(f"✗ {attempt['name']} failed with exception: {e}")

            print("All conversion methods failed")
            return False

        except Exception as e:
            print(f"ERROR: Exception during audio conversion: {e}")
            return False


# Global instance
file_conversion_service = FileConversionService()
