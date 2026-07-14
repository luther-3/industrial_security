<template>
  <div class="stats-panel">
    <StatCard label="画面总人数" :value="store.totalPersons" />
    <StatCard label="未戴安全帽的人数" :value="store.noHelmet" :isAlert="store.noHelmet > 0" />
    <StatCard label="未穿反光衣的人数" :value="store.noVest" :isAlert="store.noVest > 0" />
    <StatCard label="摔倒的人数" :value="store.fall ? 1 : 0" :isAlert="store.fall" />
    <SystemInfo
      :fps="store.fps"
      :cameraStatus="store.cameraStatus"
      :lastUpdate="store.lastUpdate"
    />
  </div>
</template>

<script setup>
import { useMonitorStore } from '../stores/monitor'
import StatCard from './StatCard.vue'
import SystemInfo from './SystemInfo.vue'

const store = useMonitorStore()
</script>

<style scoped>
.stats-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 260px;
}
</style>
