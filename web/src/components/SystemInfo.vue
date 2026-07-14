<template>
  <div class="system-info">
    <div class="info-row">
      <span class="key">帧率</span>
      <span class="val">{{ fps }}</span>
    </div>
    <div class="info-row">
      <span class="key">摄像头</span>
      <span :class="['dot', cameraStatus]"></span>
      <span class="val">{{ statusText }}</span>
    </div>
    <div class="info-row">
      <span class="key">更新时间</span>
      <span class="val time">{{ lastUpdate || '--' }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  fps: { type: Number, default: 0 },
  cameraStatus: { type: String, default: 'connecting' },
  lastUpdate: { type: String, default: null },
})

const statusText = computed(() => {
  switch (props.cameraStatus) {
    case 'connected': return '已连接'
    case 'disconnected': return '已断开'
    default: return '连接中...'
  }
})
</script>

<style scoped>
.system-info {
  background: #FFFFFF;
  border-radius: 8px;
  border: 1px solid #E4E7ED;
  padding: 16px 20px;
  font-size: 13px;
  color: #606266;
}
.info-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}
.info-row:last-child { margin-bottom: 0; }
.key { color: #909399; width: 55px; }
.val { font-weight: 500; }
.val.time { font-size: 11px; color: #C0C4CC; }
.dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: #909399;
}
.dot.connected { background: #67C23A; }
.dot.disconnected { background: #F56C6C; animation: pulse 1s infinite; }
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}
</style>
