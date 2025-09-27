<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { VoiceMediaRecorder } from './MediaRecorder';

  // Props using $props rune
  interface Props {
    websocketUrl?: string;
    chunkInterval?: number;
    autoStart?: boolean;
  }

  let { 
    websocketUrl = $bindable('ws://localhost:8000/ws/audio'),
    chunkInterval = $bindable(250),
    autoStart = false 
  }: Props = $props();

  // State using $state rune
  let recorder = $state<VoiceMediaRecorder | null>(null);
  let isRecording = $state(false);
  let hasPermission = $state(false);
  let wsConnected = $state(false);
  let error = $state('');
  let status = $state('');
  let transcriptions = $state<Array<{text: string, confidence: number, timestamp: string}>>([]);
  let batchTranscriptions = $state<Array<{text: string, confidence: number, duration: number, readyForLlm: boolean}>>([]);
  let chunksReceived = $state(0);
  let isProcessingBatch = $state(false);

  // Initialize recorder
  onMount(() => {
    recorder = new VoiceMediaRecorder(
      {
        websocketUrl,
        chunkInterval,
        mimeType: 'audio/webm;codecs=opus'
      },
      {
        onDataAvailable: (chunk) => {
          console.log(`Audio chunk ${chunk.sequenceNumber}: ${chunk.data.size} bytes`);
        },
        onError: (err) => {
          error = err.message;
          status = 'Error occurred';
        },
        onStart: () => {
          isRecording = true;
          status = 'Recording...';
          error = '';
          transcriptions = []; // Clear previous transcriptions
          batchTranscriptions = []; // Clear previous batch transcriptions
          chunksReceived = 0;
          isProcessingBatch = false;
        },
        onStop: () => {
          isRecording = false;
          status = 'Stopped';
        },
        onWebSocketConnected: () => {
          wsConnected = true;
          status = 'WebSocket connected';
        },
        onWebSocketDisconnected: () => {
          wsConnected = false;
          status = 'WebSocket disconnected';
        },
        onWebSocketError: (err) => {
          error = `WebSocket error: ${err.message}`;
          wsConnected = false;
        },
        onTranscription: (result) => {
          transcriptions = [...transcriptions, {
            text: result.text,
            confidence: result.confidence,
            timestamp: new Date(result.processedAt).toLocaleTimeString()
          }];
          status = `Transcription received: "${result.text}"`;
        },
        onAudioAck: (ack) => {
          chunksReceived++;
          status = `Chunk ${ack.sequenceNumber} processed`;
        },
        onBatchProcessing: (batchStatus) => {
          isProcessingBatch = true;
          status = batchStatus.message;
        },
        onBatchTranscription: (result) => {
          isProcessingBatch = false;
          batchTranscriptions = [...batchTranscriptions, {
            text: result.text,
            confidence: result.confidence,
            duration: result.durationSeconds,
            readyForLlm: result.readyForLlm
          }];
          status = `Batch transcription: "${result.text.substring(0, 50)}..."`;
        },
        onRecordingComplete: (summary) => {
          status = `Recording complete: ${summary.totalChunksProcessed} chunks processed`;
        }
      }
    );

    // Auto-start if enabled
    if (autoStart) {
      startRecording();
    }
  });

  // Cleanup on destroy
  onDestroy(() => {
    if (recorder) {
      recorder.cleanup();
    }
  });

  async function requestPermission() {
    if (!recorder) return false;
    const granted = await recorder.requestPermission();
    hasPermission = granted;
    if (!granted) {
      error = 'Microphone permission denied';
    }
    return granted;
  }

  async function connectWebSocket() {
    if (!recorder) return false;
    const connected = await recorder.connectWebSocket();
    if (!connected) {
      error = 'Failed to connect to WebSocket';
    }
    return connected;
  }

  async function startRecording() {
    if (!recorder) return;
    if (!hasPermission) {
      const granted = await requestPermission();
      if (!granted) return;
    }

    if (!wsConnected) {
      const connected = await connectWebSocket();
      if (!connected) return;
    }

    await recorder.startRecording();
  }

  function stopRecording() {
    if (!recorder) return;
    recorder.stopRecording();
  }

  function cleanup() {
    if (!recorder) return;
    recorder.cleanup();
    isRecording = false;
    hasPermission = false;
    wsConnected = false;
    error = '';
    status = '';
    transcriptions = [];
    batchTranscriptions = [];
    chunksReceived = 0;
    isProcessingBatch = false;
  }
</script>

<div class="max-w-md mx-auto p-5 border border-gray-300 rounded-lg font-sans">
  <div class="flex justify-between items-center mb-5">
    <h3 class="text-lg font-semibold text-gray-800 m-0">Audio Recorder</h3>
    <div class="flex gap-2">
      <span class="px-2 py-1 rounded text-xs transition-all {hasPermission ? 'bg-green-500 text-white' : 'bg-gray-200 text-gray-600'}">
        🎤 Permission
      </span>
      <span class="px-2 py-1 rounded text-xs transition-all {wsConnected ? 'bg-green-500 text-white' : 'bg-gray-200 text-gray-600'}">
        🌐 WebSocket
      </span>
      <span class="px-2 py-1 rounded text-xs transition-all {isRecording ? 'bg-green-500 text-white' : 'bg-gray-200 text-gray-600'}">
        🔴 Recording
      </span>
    </div>
  </div>

  {#if error}
    <div class="bg-red-50 text-red-700 p-3 rounded border-l-4 border-red-600 mb-4">
      ❌ {error}
    </div>
  {/if}

  {#if status}
    <div class="bg-blue-50 text-blue-700 p-3 rounded border-l-4 border-blue-600 mb-4">
      ℹ️ {status}
    </div>
  {/if}

  <div class="flex gap-2 mb-5 flex-wrap">
    {#if !hasPermission}
      <button class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-60 disabled:cursor-not-allowed transition-colors" onclick={requestPermission}>
        Grant Microphone Permission
      </button>
    {:else if !wsConnected}
      <button class="px-4 py-2 bg-orange-500 text-white rounded hover:bg-orange-600 disabled:opacity-60 disabled:cursor-not-allowed transition-colors" onclick={connectWebSocket}>
        Connect WebSocket
      </button>
    {:else if !isRecording}
      <button class="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-60 disabled:cursor-not-allowed transition-colors" onclick={startRecording}>
        Start Recording
      </button>
    {:else}
      <button class="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 disabled:opacity-60 disabled:cursor-not-allowed transition-colors" onclick={stopRecording}>
        Stop Recording
      </button>
    {/if}

    <button class="px-4 py-2 bg-transparent text-gray-600 border border-gray-300 rounded hover:bg-gray-50 transition-colors" onclick={cleanup}>
      Cleanup
    </button>
  </div>

  <div class="flex flex-col gap-3">
    <label class="flex flex-col gap-1 text-sm text-gray-600">
      WebSocket URL:
      <input 
        type="text" 
        bind:value={websocketUrl} 
        placeholder="ws://localhost:8000/ws/audio"
        disabled={isRecording}
        class="p-2 border border-gray-300 rounded disabled:bg-gray-100 disabled:text-gray-500"
      />
    </label>
    
    <label class="flex flex-col gap-1 text-sm text-gray-600">
      Chunk Interval (ms):
      <input 
        type="number" 
        bind:value={chunkInterval} 
        min="100" 
        max="1000" 
        step="50"
        disabled={isRecording}
        class="p-2 border border-gray-300 rounded disabled:bg-gray-100 disabled:text-gray-500"
      />
    </label>
  </div>

  <!-- Batch Processing Status -->
  {#if isProcessingBatch}
    <div class="mt-4">
      <div class="bg-yellow-50 border border-yellow-200 rounded p-3">
        <div class="text-sm text-yellow-800 font-medium">
          🔄 Processing audio batch...
        </div>
        <div class="text-xs text-yellow-600 mt-1">
          Combining chunks for transcription
        </div>
      </div>
    </div>
  {/if}

  <!-- Batch Transcription Results -->
  {#if batchTranscriptions.length > 0}
    <div class="mt-5">
      <h4 class="text-md font-semibold text-gray-800 mb-3">Batch Transcriptions (Ready for LLM)</h4>
      <div class="max-h-64 overflow-y-auto space-y-3">
        {#each batchTranscriptions as transcription, index}
          <div class="bg-blue-50 border border-blue-200 rounded p-4">
            <div class="flex justify-between items-start mb-2">
              <div class="text-sm text-blue-800 font-medium">
                Batch #{index + 1}
              </div>
              {#if transcription.readyForLlm}
                <span class="bg-green-100 text-green-800 text-xs px-2 py-1 rounded">
                  Ready for LLM
                </span>
              {/if}
            </div>
            <div class="text-sm text-blue-900 mb-2">
              {transcription.text}
            </div>
            <div class="text-xs text-blue-600">
              Confidence: {Math.round(transcription.confidence * 100)}% • 
              Duration: {transcription.duration}s
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/if}

  <!-- Real-time Transcription Results -->
  {#if transcriptions.length > 0}
    <div class="mt-5">
      <h4 class="text-md font-semibold text-gray-800 mb-3">Real-time Transcriptions</h4>
      <div class="max-h-48 overflow-y-auto space-y-2">
        {#each transcriptions as transcription, index}
          <div class="bg-green-50 border border-green-200 rounded p-3">
            <div class="text-sm text-green-800 font-medium">
              {transcription.text}
            </div>
            <div class="text-xs text-green-600 mt-1">
              Confidence: {Math.round(transcription.confidence * 100)}% • {transcription.timestamp}
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/if}

  <!-- Statistics -->
  <div class="mt-4 text-sm text-gray-600">
    <p>Chunks processed: {chunksReceived}</p>
    <p>Real-time transcriptions: {transcriptions.length}</p>
    <p>Batch transcriptions: {batchTranscriptions.length}</p>
    <p>Ready for LLM processing: {batchTranscriptions.filter(t => t.readyForLlm).length}</p>
  </div>
</div>

