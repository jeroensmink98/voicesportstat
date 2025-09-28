<script lang="ts">
	// Props using Svelte 5 conventions
	interface Props {
		hasPermission: boolean;
		wsConnected: boolean;
		isRecording: boolean;
	}

	let { hasPermission, wsConnected, isRecording } = $props() as Props;
</script>

<div class="flex justify-between items-center mb-5">
	<h3 class="text-lg font-semibold text-gray-800 m-0">Audio Recorder</h3>
	<div class="flex gap-2">
		<span
			class="px-2 py-1 rounded text-xs transition-all {hasPermission
				? 'bg-green-500 text-white'
				: 'bg-gray-200 text-gray-600'}"
		>
			🎤 Permission
		</span>
		<span
			class="px-2 py-1 rounded text-xs transition-all {wsConnected
				? 'bg-green-500 text-white'
				: 'bg-gray-200 text-gray-600'}"
		>
			🌐 WebSocket
		</span>
		<span
			class="px-2 py-1 rounded text-xs transition-all {isRecording
				? 'bg-green-500 text-white'
				: 'bg-gray-200 text-gray-600'}"
		>
			🔴 Recording
		</span>
	</div>
</div>

