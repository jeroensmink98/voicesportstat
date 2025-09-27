# VoiceMediaRecorder

A TypeScript class for recording audio from the user's microphone and streaming it over WebSocket with timestamps.

## Features

- 🎤 **Microphone Recording**: Records audio using the native MediaRecorder API
- 🌐 **WebSocket Streaming**: Streams audio chunks to a backend server in real-time
- ⏱️ **Timestamp Tracking**: Each audio chunk includes a timestamp and sequence number
- 🔧 **Configurable**: Customizable chunk intervals, bitrates, and MIME types
- 🛡️ **Error Handling**: Comprehensive error handling and user permission management
- 📱 **Cross-browser**: Works with modern browsers supporting MediaRecorder API

## Quick Start

### Basic Usage

```typescript
import { createVoiceMediaRecorder } from '$lib/MediaRecorder';

const recorder = createVoiceMediaRecorder(
	{
		websocketUrl: 'ws://localhost:8000/ws/audio',
		chunkInterval: 250 // milliseconds
	},
	{
		onDataAvailable: (chunk) => {
			console.log(`Chunk ${chunk.sequenceNumber}: ${chunk.data.size} bytes`);
		},
		onError: (error) => {
			console.error('Recording error:', error);
		}
	}
);

// Start recording
await recorder.connectWebSocket();
await recorder.startRecording();

// Stop recording
recorder.stopRecording();
```

### Using the Svelte Component

```svelte
<script>
	import AudioRecorder from '$lib/MediaRecorder/AudioRecorder.svelte';
</script>

<AudioRecorder websocketUrl="ws://localhost:8000/ws/audio" chunkInterval={250} />
```

## API Reference

### VoiceMediaRecorder Class

#### Constructor

```typescript
new VoiceMediaRecorder(config?: MediaRecorderConfig, events?: MediaRecorderEvents)
```

#### Configuration Options

```typescript
interface MediaRecorderConfig {
	mimeType?: string; // Audio format (default: 'audio/webm;codecs=opus')
	audioBitsPerSecond?: number; // Audio quality (default: 128000)
	chunkInterval?: number; // Milliseconds between chunks (default: 250)
	websocketUrl?: string; // WebSocket server URL
}
```

#### Event Handlers

```typescript
interface MediaRecorderEvents {
	onDataAvailable?: (chunk: AudioChunk) => void;
	onError?: (error: Error) => void;
	onStart?: () => void;
	onStop?: () => void;
	onWebSocketConnected?: () => void;
	onWebSocketDisconnected?: () => void;
	onWebSocketError?: (error: Error) => void;
}
```

#### Audio Chunk Format

```typescript
interface AudioChunk {
	data: Blob; // The audio data
	timestamp: number; // Unix timestamp in milliseconds
	sequenceNumber: number; // Incremental sequence number
}
```

### Methods

#### `requestPermission(): Promise<boolean>`

Requests microphone permission from the user.

#### `connectWebSocket(url?: string): Promise<boolean>`

Connects to the WebSocket server.

#### `startRecording(): Promise<boolean>`

Starts recording audio. Returns `true` if successful.

#### `stopRecording(): void`

Stops the current recording session.

#### `disconnectWebSocket(): void`

Disconnects from the WebSocket server.

#### `cleanup(): void`

Cleans up all resources (stops recording, disconnects WebSocket, stops media tracks).

#### `getRecordingStatus(): RecordingStatus`

Returns the current status of the recorder.

#### `updateConfig(newConfig: Partial<MediaRecorderConfig>): void`

Updates the recorder configuration.

#### `updateEvents(newEvents: MediaRecorderEvents): void`

Updates the event handlers.

## WebSocket Message Format

The recorder sends audio chunks to the WebSocket server in the following format:

```json
{
	"type": "audio_chunk",
	"data": [
		/* Array of bytes */
	],
	"timestamp": 1640995200000,
	"sequenceNumber": 1,
	"mimeType": "audio/webm;codecs=opus"
}
```

## Browser Compatibility

- **Chrome/Edge**: Full support
- **Firefox**: Full support
- **Safari**: Limited support (may need fallback MIME types)
- **Mobile browsers**: Generally supported

## Error Handling

The recorder handles various error scenarios:

- Microphone permission denied
- WebSocket connection failures
- MediaRecorder API errors
- Browser compatibility issues

All errors are passed to the `onError` or `onWebSocketError` event handlers.

## Example Backend Integration

Here's how you might handle the audio chunks on your FastAPI backend:

```python
import asyncio
import json
from fastapi import WebSocket

async def handle_audio_websocket(websocket: WebSocket):
    await websocket.accept()

    while True:
        try:
            # Receive audio chunk
            data = await websocket.receive_text()
            message = json.loads(data)

            if message["type"] == "audio_chunk":
                # Convert bytes back to audio data
                audio_bytes = bytes(message["data"])
                timestamp = message["timestamp"]
                sequence = message["sequenceNumber"]

                # Process audio for transcription
                transcription = await transcribe_audio(audio_bytes)

                # Send transcription back
                await websocket.send_text(json.dumps({
                    "type": "transcription",
                    "text": transcription,
                    "timestamp": timestamp,
                    "sequenceNumber": sequence
                }))

        except Exception as e:
            print(f"WebSocket error: {e}")
            break
```

## Development

To run the development server:

```bash
cd client
pnpm install
pnpm dev
```

The MediaRecorder will be available at `http://localhost:5173` with the AudioRecorder component integrated into the main page.
