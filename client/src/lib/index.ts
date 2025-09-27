// place files you want to import through the `$lib` alias in this folder.

// MediaRecorder exports
export {
	VoiceMediaRecorder,
	createVoiceMediaRecorder,
	type AudioChunk,
	type MediaRecorderConfig,
	type MediaRecorderEvents,
	type TranscriptionResult,
	type AudioAck,
	type BatchTranscriptionResult,
	type BatchProcessingStatus,
	type RecordingSummary
} from './MediaRecorder/MediaRecorder';

// Component exports
export { default as BatchTranscriptions } from './components/BatchTranscriptions.svelte';
export { default as RecordingStatus } from './components/RecordingStatus.svelte';
export { default as ConnectionInfo } from './components/ConnectionInfo.svelte';
