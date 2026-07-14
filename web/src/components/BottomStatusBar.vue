<template>
  <div class="bottom-bar">
    <span>摄像头: {{ statusText }}</span>
    <span>帧率: {{ store.fps }}</span>
    <span class="muted">工业安防监测系统 v1.0</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useMonitorStore } from '../stores/monitor'
const store = useMonitorStore()
const statusText = computed(() => {
  switch (store.cameraStatus) {
    case 'connected': return '已连接'
    case 'disconnected': return '已断开'
    default: return '连接中...'
  }
})
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
