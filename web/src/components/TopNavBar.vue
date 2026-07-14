<template>
  <div class="top-nav">
    <div class="left">
      <span class="icon">&#9673;</span>
      <span class="title">工业安防监测系统</span>
    </div>
    <div class="right">
      <span :class="['dot', store.systemStatus]"></span>
      <span class="status-text">{{ store.systemStatus === 'alarming' ? '告警中' : '运行中' }}</span>
    </div>
  </div>
</template>

<script setup>
import { useMonitorStore } from '../stores/monitor'
const store = useMonitorStore()
</script>

<style scoped>
.top-nav {
  height: 56px;
  background: #FFFFFF;
  border-bottom: 1px solid #E4E7ED;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}
.left {
  display: flex;
  align-items: center;
  gap: 10px;
}
.icon { font-size: 20px; color: #409EFF; }
.title { font-size: 18px; font-weight: 600; color: #303133; }
.right {
  display: flex;
  align-items: center;
  gap: 8px;
}
.dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: #67C23A;
}
.dot.alarming {
  background: #F56C6C;
  animation: pulse 1s ease-in-out infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1.0); }
  50% { opacity: 0.6; transform: scale(1.3); }
}
.status-text {
  font-size: 13px;
  font-weight: 500;
  color: #909399;
}
</style>
