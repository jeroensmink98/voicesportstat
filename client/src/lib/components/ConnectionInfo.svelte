<script lang="ts">
	// Props using Svelte 5 conventions
	interface Props {
		hasPermission: boolean;
		wsConnected: boolean;
		isRecording: boolean;
		permissionInfo: {
			hasPermission: boolean;
			age: number | null;
			isExpiringSoon: boolean;
		};
		onRevokePermission: () => void;
	}

	let { hasPermission, wsConnected, isRecording, permissionInfo, onRevokePermission } =
		$props() as Props;
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

<!-- Permission Info Display -->
{#if permissionInfo.hasPermission}
	<div class="bg-green-50 border border-green-200 rounded p-3 mb-4">
		<div class="flex justify-between items-center">
			<div class="text-sm text-green-800">
				<div class="font-medium">✅ Microphone permission granted</div>
				{#if permissionInfo.age !== null}
					<div class="text-xs text-green-600 mt-1">
						Saved {permissionInfo.age} day{permissionInfo.age !== 1 ? 's' : ''} ago
						{#if permissionInfo.isExpiringSoon}
							<span class="text-orange-600 font-medium">(expires soon)</span>
						{/if}
					</div>
				{/if}
			</div>
			<button
				class="px-3 py-1 bg-red-100 text-red-700 text-xs rounded hover:bg-red-200 transition-colors"
				on:click={onRevokePermission}
				title="Revoke and clear saved permission"
			>
				Revoke
			</button>
		</div>
	</div>
{/if}
