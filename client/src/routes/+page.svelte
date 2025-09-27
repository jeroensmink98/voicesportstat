<script>
  import AudioRecorder from '$lib/MediaRecorder/AudioRecorder.svelte';
</script>

<div class="container">
  <h1 class="text-3xl font-bold underline mb-8">Voice Sport Stat</h1>
  <p class="mb-6">Record audio from your microphone and stream it to the backend for transcription.</p>
  
  <AudioRecorder
    websocketUrl="ws://localhost:8000/ws/audio"
    chunkInterval={1000}
  />
</div>

<style>
  .container {
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
  }
</style>