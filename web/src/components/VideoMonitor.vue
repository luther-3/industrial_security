<template>
  <div class="video-container">
    <img :src="streamUrl" alt="Live Stream" />
    <AlertOverlay :visible="store.fall" />
  </div>
</template>

<script setup>
import { useMonitorStore } from '../stores/monitor'
import AlertOverlay from './AlertOverlay.vue'

const store = useMonitorStore()
// Use origin-based URL so Vite doesn't try to resolve it during build
const streamUrl = window.location.origin + '/stream/video'
</script>

<style scoped>
.video-container {
  position: relative;
  background: #000;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #DCDFE6;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
}
.video-container img {
  width: 100%;
  height: auto;
  display: block;
}
</style>
