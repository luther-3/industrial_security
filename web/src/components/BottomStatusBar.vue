<template>
  <div class="bottom-bar">
    <span>Camera: {{ store.cameraStatus }}</span>
    <span>FPS: {{ store.fps }}</span>
    <span class="muted">Industrial Security Monitor v1.0</span>
  </div>
</template>

<script setup>
import { useMonitorStore } from '../stores/monitor'
const store = useMonitorStore()
</script>

<style scoped>
.bottom-bar {
  height: 32px;
  background: #FFFFFF;
  border-top: 1px solid #E4E7ED;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  font-size: 12px;
  color: #909399;
}
.muted { color: #C0C4CC; }
</style>
