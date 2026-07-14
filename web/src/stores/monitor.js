import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useMonitorStore = defineStore('monitor', () => {
  // --- state ---
  const totalPersons = ref(0)
  const noHelmet = ref(0)
  const noVest = ref(0)
  const fall = ref(false)
  const cameraStatus = ref('connecting')   // 'connected' | 'disconnected' | 'connecting'
  const fps = ref(0)
  const lastUpdate = ref(null)

  // --- getters ---
  const hasViolation = computed(() => noHelmet.value > 0 || noVest.value > 0)
  const hasAnyAlert = computed(() => hasViolation.value || fall.value)
  const systemStatus = computed(() => hasAnyAlert.value ? 'alarming' : 'running')

  // --- actions ---
  function updateFromServer(data) {
    totalPersons.value = data.total_persons ?? 0
    noHelmet.value = data.no_helmet ?? 0
    noVest.value = data.no_vest ?? 0
    fall.value = data.fall ?? false
    cameraStatus.value = data.camera_status ?? 'connecting'
    fps.value = data.fps ?? 0
    lastUpdate.value = data.timestamp ?? null
  }

  return {
    totalPersons, noHelmet, noVest, fall,
    cameraStatus, fps, lastUpdate,
    hasViolation, hasAnyAlert, systemStatus,
    updateFromServer,
  }
})
