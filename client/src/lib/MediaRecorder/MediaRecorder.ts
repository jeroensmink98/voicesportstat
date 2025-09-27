export interface AudioChunk {
	data: Blob;
	timestamp: number;
	sequenceNumber: number;
}

export interface MediaRecorderConfig {
	mimeType?: string;
	audioBitsPerSecond?: number;
	chunkInterval?: number; // milliseconds between chunks
	websocketUrl?: string;
	language?: string; // language code for transcription (e.g., 'en', 'nl', 'de')
}

export interface MediaRecorderEvents {
	onDataAvailable?: (chunk: AudioChunk) => void;
	onError?: (error: Error) => void;
	onStart?: () => void;
	onStop?: () => void;
	onWebSocketConnected?: () => void;
	onWebSocketDisconnected?: () => void;
	onWebSocketError?: (error: Error) => void;
	onTranscription?: (result: TranscriptionResult) => void;
	onAudioAck?: (ack: AudioAck) => void;
	onBatchTranscription?: (result: BatchTranscriptionResult) => void;
	onBatchProcessing?: (status: BatchProcessingStatus) => void;
	onRecordingComplete?: (summary: RecordingSummary) => void;
	onPermissionChanged?: (granted: boolean) => void;
}

export interface TranscriptionResult {
	sequenceNumber: number;
	timestamp: number;
	text: string;
	confidence: number;
	processedAt: string;
}

export interface AudioAck {
	sequenceNumber: number;
	timestamp: number;
	message: string;
	processedAt: string;
}

export interface BatchTranscriptionResult {
	text: string;
	confidence: number;
	chunkCount: number;
	durationSeconds: number;
	timestamp: string;
	readyForLlm: boolean;
}

export interface BatchProcessingStatus {
	message: string;
	timestamp: string;
}

export interface RecordingSummary {
	message: string;
	totalChunksProcessed: number;
	timestamp: string;
}

export class VoiceMediaRecorder {
	private mediaRecorder: MediaRecorder | null = null;
	private mediaStream: MediaStream | null = null;
	private websocket: WebSocket | null = null;
	private sequenceNumber = 0;
	private isRecording = false;
	private hasPermission = false;
	private config: Required<MediaRecorderConfig>;
	private events: MediaRecorderEvents;

	constructor(config: MediaRecorderConfig = {}, events: MediaRecorderEvents = {}) {
		this.config = {
			mimeType: config.mimeType || 'audio/wav',
			audioBitsPerSecond: config.audioBitsPerSecond || 128000,
			chunkInterval: config.chunkInterval || 250,
			websocketUrl: config.websocketUrl || '',
			language: config.language || 'en' // default to English
		};
		this.events = events;
	}

	/**
	 * Request microphone permission and initialize the media stream
	 */
	async requestPermission(): Promise<boolean> {
		try {
			this.mediaStream = await navigator.mediaDevices.getUserMedia({
				audio: {
					echoCancellation: true,
					noiseSuppression: true,
					autoGainControl: true,
					sampleRate: 44100
				}
			});
			this.hasPermission = true;
			this.events.onPermissionChanged?.(true);
			return true;
		} catch (error) {
			const err = error instanceof Error ? error : new Error('Failed to access microphone');
			this.hasPermission = false;
			this.events.onPermissionChanged?.(false);
			this.events.onError?.(err);
			return false;
		}
	}

	/**
	 * Check if we currently have microphone permission
	 */
	getPermissionStatus(): boolean {
		return this.hasPermission;
	}

	/**
	 * Connect to WebSocket server
	 */
	async connectWebSocket(url?: string): Promise<boolean> {
		const wsUrl = url || this.config.websocketUrl;
		if (!wsUrl) {
			const error = new Error('WebSocket URL not provided');
			this.events.onWebSocketError?.(error);
			return false;
		}

		return new Promise((resolve) => {
			try {
				this.websocket = new WebSocket(wsUrl);

				this.websocket.onopen = () => {
					this.events.onWebSocketConnected?.();
					resolve(true);
				};

				this.websocket.onerror = () => {
					const err = new Error('WebSocket connection failed');
					this.events.onWebSocketError?.(err);
					resolve(false);
				};

				this.websocket.onclose = () => {
					this.events.onWebSocketDisconnected?.();
				};

				this.websocket.onmessage = (event) => {
					this.handleWebSocketMessage(event.data);
				};
			} catch (error) {
				const err =
					error instanceof Error ? error : new Error('Failed to create WebSocket connection');
				this.events.onWebSocketError?.(err);
				resolve(false);
			}
		});
	}

	/**
	 * Start recording audio
	 */
	async startRecording(currentLanguage?: string): Promise<boolean> {
		if (this.isRecording) {
			console.warn('Recording is already in progress');
			return true;
		}

		// Use the provided language or fall back to config
		const languageToUse = currentLanguage || this.config.language;
		console.log(`Starting recording with language: ${languageToUse}`);

		// Ensure we have permission and media stream
		if (!this.mediaStream || !this.hasPermission) {
			const hasPermission = await this.requestPermission();
			if (!hasPermission) {
				return false;
			}
		}

		try {
			// Ensure a fresh WebSocket connection per recording session
			if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
				const connected = await this.connectWebSocket();
				if (!connected) {
					throw new Error('Failed to connect WebSocket');
				}
			}

			// Check if the browser supports the desired mime type
			if (!MediaRecorder.isTypeSupported(this.config.mimeType)) {
				// Fallback to a more widely supported format
				this.config.mimeType = 'audio/wav';
				if (!MediaRecorder.isTypeSupported(this.config.mimeType)) {
					// Try WebM as fallback (though we prefer WAV)
					this.config.mimeType = 'audio/webm;codecs=opus';
					if (!MediaRecorder.isTypeSupported(this.config.mimeType)) {
						this.config.mimeType = 'audio/webm';
					}
				}
			}

			console.log(`Using audio format: ${this.config.mimeType}`);

			this.mediaRecorder = new MediaRecorder(this.mediaStream!, {
				mimeType: this.config.mimeType,
				audioBitsPerSecond: this.config.audioBitsPerSecond
			});

			this.mediaRecorder.ondataavailable = (event) => {
				if (event.data.size > 0) {
					const audioChunk: AudioChunk = {
						data: event.data,
						timestamp: Date.now(),
						sequenceNumber: this.sequenceNumber++
					};

					// Send to WebSocket if connected
					if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
						this.sendAudioChunk(audioChunk);
					}

					// Call user-provided callback
					this.events.onDataAvailable?.(audioChunk);
				}
			};

			this.mediaRecorder.onerror = (event) => {
				const error = new Error(`MediaRecorder error: ${event}`);
				this.events.onError?.(error);
			};

			this.mediaRecorder.onstop = () => {
				this.isRecording = false;
				this.events.onStop?.();
			};

			this.mediaRecorder.start(this.config.chunkInterval);
			this.isRecording = true;

			// Send start recording message with language information
			this.sendStartRecordingMessage(languageToUse);

			this.events.onStart?.();

			return true;
		} catch (error) {
			const err = error instanceof Error ? error : new Error('Failed to start recording');
			this.events.onError?.(err);
			return false;
		}
	}

	/**
	 * Stop recording audio
	 */
	stopRecording(): void {
		if (!this.isRecording || !this.mediaRecorder) {
			console.warn('No recording in progress');
			return;
		}

		this.mediaRecorder.stop();

		// Send end recording message to server
		this.sendEndRecordingMessage();

		// Disconnect the WebSocket so the next start creates a new server session
		this.disconnectWebSocket();
	}

	/**
	 * Send start recording message to WebSocket server with language information
	 */
	private sendStartRecordingMessage(languageToUse?: string): void {
		if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
			console.warn('WebSocket not connected, cannot send start recording message');
			return;
		}

		try {
			const language = languageToUse || this.config.language;
			const message = {
				type: 'start_recording',
				language: language,
				timestamp: Date.now()
			};

			this.websocket.send(JSON.stringify(message));
			console.log(`Sent start recording message with language: ${language}`);
			console.log('Full message:', message);
		} catch (error) {
			console.error('Failed to send start recording message:', error);
			this.events.onWebSocketError?.(new Error('Failed to send start recording message'));
		}
	}

	/**
	 * Send end recording message to WebSocket server
	 */
	private sendEndRecordingMessage(): void {
		if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
			console.warn('WebSocket not connected, cannot send end recording message');
			return;
		}

		try {
			const message = {
				type: 'end_recording',
				timestamp: Date.now()
			};

			this.websocket.send(JSON.stringify(message));
		} catch (error) {
			console.error('Failed to send end recording message:', error);
			this.events.onWebSocketError?.(new Error('Failed to send end recording message'));
		}
	}

	/**
	 * Handle incoming WebSocket messages from the server
	 */
	private handleWebSocketMessage(data: string): void {
		try {
			const message = JSON.parse(data);

			switch (message.type) {
				case 'connection':
					console.log('WebSocket connected:', message.message);
					break;

				case 'audio_ack':
					console.log(`Audio chunk ${message.sequenceNumber} acknowledged`);
					this.events.onAudioAck?.({
						sequenceNumber: message.sequenceNumber,
						timestamp: message.timestamp,
						message: message.message,
						processedAt: message.processed_at
					});
					break;

				case 'transcription':
					console.log(`Transcription for chunk ${message.sequenceNumber}:`, message.text);
					this.events.onTranscription?.({
						sequenceNumber: message.sequenceNumber,
						timestamp: message.timestamp,
						text: message.text,
						confidence: message.confidence,
						processedAt: message.processed_at
					});
					break;

				case 'error':
					console.error('Server error:', message.message);
					this.events.onError?.(new Error(`Server error: ${message.message}`));
					break;

				case 'recording_started':
					console.log('Recording session started on server');
					break;

				case 'recording_stopped':
					console.log('Recording session stopped on server');
					break;

				case 'batch_processing':
					console.log('Batch processing:', message.message);
					this.events.onBatchProcessing?.({
						message: message.message,
						timestamp: message.timestamp
					});
					break;

				case 'batch_transcription':
					console.log('Batch transcription received:', message.text);
					this.events.onBatchTranscription?.({
						text: message.text,
						confidence: message.confidence,
						chunkCount: message.chunk_count,
						durationSeconds: message.duration_seconds,
						timestamp: message.timestamp,
						readyForLlm: message.ready_for_llm
					});
					break;

				case 'recording_complete':
					console.log('Recording complete:', message.message);
					this.events.onRecordingComplete?.({
						message: message.message,
						totalChunksProcessed: message.total_chunks_processed,
						timestamp: message.timestamp
					});
					break;

				default:
					console.log('Unknown message type:', message.type);
			}
		} catch (error) {
			console.error('Failed to parse WebSocket message:', error);
			this.events.onError?.(new Error('Failed to parse server message'));
		}
	}

	/**
	 * Send audio chunk to WebSocket server
	 */
	private sendAudioChunk(chunk: AudioChunk): void {
		if (!this.websocket || this.websocket.readyState !== WebSocket.OPEN) {
			console.warn('WebSocket not connected, cannot send audio chunk');
			return;
		}

		try {
			// Convert blob to array buffer for transmission
			chunk.data
				.arrayBuffer()
				.then((arrayBuffer) => {
					const message = {
						type: 'audio_chunk',
						data: Array.from(new Uint8Array(arrayBuffer)),
						timestamp: chunk.timestamp,
						sequenceNumber: chunk.sequenceNumber,
						mimeType: this.config.mimeType
					};

					this.websocket!.send(JSON.stringify(message));
				})
				.catch((error) => {
					console.error('Failed to convert blob to array buffer:', error);
					this.events.onWebSocketError?.(new Error('Failed to process audio data'));
				});
		} catch (error) {
			const err = error instanceof Error ? error : new Error('Failed to send audio chunk');
			this.events.onWebSocketError?.(err);
		}
	}

	/**
	 * Disconnect WebSocket
	 */
	disconnectWebSocket(): void {
		if (this.websocket) {
			this.websocket.close();
			this.websocket = null;
		}
	}

	/**
	 * Clean up resources
	 */
	cleanup(): void {
		this.stopRecording();
		this.disconnectWebSocket();

		if (this.mediaStream) {
			this.mediaStream.getTracks().forEach((track) => track.stop());
			this.mediaStream = null;
		}

		this.mediaRecorder = null;
		this.sequenceNumber = 0;
		this.isRecording = false;
		this.hasPermission = false;
	}

	/**
	 * Get current recording status
	 */
	getRecordingStatus(): {
		isRecording: boolean;
		hasPermission: boolean;
		websocketConnected: boolean;
		mimeType: string;
	} {
		return {
			isRecording: this.isRecording,
			hasPermission: this.hasPermission,
			websocketConnected: this.websocket?.readyState === WebSocket.OPEN,
			mimeType: this.config.mimeType
		};
	}

	/**
	 * Update configuration
	 */
	updateConfig(newConfig: Partial<MediaRecorderConfig>): void {
		this.config = { ...this.config, ...newConfig };
	}

	/**
	 * Update event handlers
	 */
	updateEvents(newEvents: MediaRecorderEvents): void {
		this.events = { ...this.events, ...newEvents };
	}
}

// Export a default instance for convenience
export const createVoiceMediaRecorder = (
	config?: MediaRecorderConfig,
	events?: MediaRecorderEvents
) => new VoiceMediaRecorder(config, events);

// Types are already exported above as interfaces
