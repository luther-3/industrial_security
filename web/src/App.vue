<template>
  <div class="app-container">
    <TopNavBar />
    <div class="main-content">
      <div class="video-section">
        <VideoMonitor />
      </div>
      <div class="stats-section">
        <StatsPanel />
      </div>
    </div>
    <BottomStatusBar />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useMonitorStore } from './stores/monitor'
import { useWebSocket } from './composables/useWebSocket'
import TopNavBar from './components/TopNavBar.vue'
import VideoMonitor from './components/VideoMonitor.vue'
import StatsPanel from './components/StatsPanel.vue'
import BottomStatusBar from './components/BottomStatusBar.vue'

const store = useMonitorStore()
const { connect } = useWebSocket(
  `ws://${window.location.host}/ws/stats`,
  (data) => store.updateFromServer(data)
)
onMounted(() => connect())
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC',
    'Microsoft YaHei', 'Helvetica Neue', Arial, sans-serif;
  background: #F0F2F5;
  color: #303133;
}
.app-container { display: flex; flex-direction: column; min-height: 100vh; }
.main-content { display: flex; flex: 1; padding: 24px; gap: 24px; }
.video-section { flex: 0 0 65%; max-width: 65%; }
.stats-section { flex: 1; }
@media (max-width: 1279px) {
  .main-content { flex-direction: column; }
  .video-section { flex: none; max-width: 100%; }
}
</style>
