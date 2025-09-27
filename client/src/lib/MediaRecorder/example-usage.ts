// Example usage of VoiceMediaRecorder
import { VoiceMediaRecorder, createVoiceMediaRecorder } from './MediaRecorder';

// Example 1: Basic usage with WebSocket
async function basicExample() {
  const recorder = createVoiceMediaRecorder(
    {
      websocketUrl: 'ws://localhost:8000/ws/audio',
      chunkInterval: 250,
      mimeType: 'audio/webm;codecs=opus'
    },
    {
      onDataAvailable: (chunk) => {
        console.log(`Received audio chunk ${chunk.sequenceNumber} at ${new Date(chunk.timestamp).toISOString()}`);
      },
      onError: (error) => {
        console.error('Recording error:', error);
      },
      onStart: () => {
        console.log('Recording started');
      },
      onStop: () => {
        console.log('Recording stopped');
      },
      onWebSocketConnected: () => {
        console.log('WebSocket connected');
      },
      onWebSocketDisconnected: () => {
        console.log('WebSocket disconnected');
      }
    }
  );

  // Connect to WebSocket
  const connected = await recorder.connectWebSocket();
  if (!connected) {
    console.error('Failed to connect to WebSocket');
    return;
  }

  // Start recording
  const started = await recorder.startRecording();
  if (started) {
    console.log('Recording started successfully');
    
    // Stop recording after 10 seconds
    setTimeout(() => {
      recorder.stopRecording();
    }, 10000);
  }
}

// Example 2: Advanced usage with custom configuration
async function advancedExample() {
  const recorder = new VoiceMediaRecorder(
    {
      websocketUrl: 'wss://your-backend.com/ws/audio',
      chunkInterval: 100, // Smaller chunks for lower latency
      audioBitsPerSecond: 64000, // Lower bitrate
      mimeType: 'audio/webm;codecs=opus'
    },
    {
      onDataAvailable: (chunk) => {
        // Custom processing of audio chunks
        console.log(`Chunk ${chunk.sequenceNumber}: ${chunk.data.size} bytes`);
        
        // You could also store chunks locally for backup
        // localStorage.setItem(`audio_chunk_${chunk.sequenceNumber}`, JSON.stringify({
        //   timestamp: chunk.timestamp,
        //   size: chunk.data.size
        // }));
      },
      onError: (error) => {
        console.error('Recorder error:', error);
        // Handle error appropriately
      },
      onWebSocketError: (error) => {
        console.error('WebSocket error:', error);
        // Implement reconnection logic here
      }
    }
  );

  try {
    // Request microphone permission first
    const hasPermission = await recorder.requestPermission();
    if (!hasPermission) {
      console.error('Microphone permission denied');
      return;
    }

    // Connect to WebSocket
    const wsConnected = await recorder.connectWebSocket();
    if (!wsConnected) {
      console.error('WebSocket connection failed');
      return;
    }

    // Start recording
    const recordingStarted = await recorder.startRecording();
    if (!recordingStarted) {
      console.error('Failed to start recording');
      return;
    }

    console.log('Advanced recording setup complete');

    // Example: Stop recording after user interaction
    // document.getElementById('stopButton')?.addEventListener('click', () => {
    //   recorder.stopRecording();
    //   recorder.cleanup();
    // });

  } catch (error) {
    console.error('Setup failed:', error);
    recorder.cleanup();
  }
}

// Example 3: Recording without WebSocket (for local processing)
async function localRecordingExample() {
  const recorder = createVoiceMediaRecorder(
    {
      chunkInterval: 500, // Larger chunks for local storage
      mimeType: 'audio/webm'
    },
    {
      onDataAvailable: (chunk) => {
        // Process chunks locally
        console.log(`Local chunk: ${chunk.sequenceNumber}, size: ${chunk.data.size} bytes`);
        
        // Convert to audio URL for playback
        const audioUrl = URL.createObjectURL(chunk.data);
        console.log('Audio URL:', audioUrl);
        
        // Clean up URL after use
        setTimeout(() => URL.revokeObjectURL(audioUrl), 1000);
      },
      onError: (error) => {
        console.error('Local recording error:', error);
      }
    }
  );

  const started = await recorder.startRecording();
  if (started) {
    console.log('Local recording started');
    
    // Stop after 5 seconds
    setTimeout(() => {
      recorder.stopRecording();
      recorder.cleanup();
    }, 5000);
  }
}

// Export examples for use in components
export { basicExample, advancedExample, localRecordingExample };
