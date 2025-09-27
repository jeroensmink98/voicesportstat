<script lang="ts">
	// Props using Svelte 5 conventions
	interface Props {
		error: string;
		status: string;
		isProcessingBatch: boolean;
	}

	let { error, status, isProcessingBatch } = $props() as Props;
</script>

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

<!-- Batch Processing Status -->
{#if isProcessingBatch}
	<div class="mt-4">
		<div class="bg-yellow-50 border border-yellow-200 rounded p-3">
			<div class="text-sm text-yellow-800 font-medium">🔄 Processing audio batch...</div>
			<div class="text-xs text-yellow-600 mt-1">Combining chunks for transcription</div>
		</div>
	</div>
{/if}
