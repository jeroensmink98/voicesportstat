<script lang="ts">
	// Props using Svelte 5 conventions
	interface BatchTranscription {
		text: string;
		confidence: number;
		duration: number;
		readyForLlm: boolean;
	}

	interface Props {
		batchTranscriptions: BatchTranscription[];
	}

	let { batchTranscriptions } = $props() as Props;
</script>

<!-- Batch Transcription Results -->
{#if batchTranscriptions.length > 0}
	<div class="mt-5">
		<h4 class="text-md font-semibold text-gray-800 mb-3">Batch Transcriptions (Ready for LLM)</h4>
		<div class="max-h-96 overflow-y-auto grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
			{#each batchTranscriptions as transcription, index (index)}
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
						Confidence: {Math.round(transcription.confidence * 100)}% • Duration: {transcription.duration}s
					</div>
				</div>
			{/each}
		</div>
	</div>
{/if}
