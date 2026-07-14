<template>
  <div class="stats-panel">
    <StatCard label="Total Persons" :value="store.totalPersons" />
    <StatCard label="No Helmet" :value="store.noHelmet" :isAlert="store.noHelmet > 0" />
    <StatCard label="No Vest" :value="store.noVest" :isAlert="store.noVest > 0" />
    <StatCard label="Fall" :value="store.fall ? 1 : 0" :isAlert="store.fall" />
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
