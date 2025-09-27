<script>
  import AudioRecorder from '$lib/MediaRecorder/AudioRecorder.svelte';

  let selectedLanguage = $state('en');

  // Debug: Watch for language changes
  $effect(() => {
    console.log(`Selected language changed to: ${selectedLanguage}`);
  });
</script>

<div class="container wide">
  <h1 class="text-3xl font-bold underline mb-8">Voice Sport Stat</h1>
  <p class="mb-6">Record audio from your microphone and stream it to the backend for transcription.</p>

  <!-- Language Selection -->
  <div class="mb-6">
    <label for="language-select" class="block text-sm font-medium text-gray-700 mb-2">
      Select Language:
    </label>
    <select
      id="language-select"
      bind:value={selectedLanguage}
      class="px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
    >
      <option value="en">English</option>
      <option value="nl">Dutch</option>
      <option value="de">German</option>
    </select>
  </div>

  <AudioRecorder
    websocketUrl="ws://localhost:8000/ws/audio"
    chunkInterval={1000}
    language={selectedLanguage}
  />
</div>

<style>
  .container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
  }

  .wide {
    width: 100%;
  }
</style>