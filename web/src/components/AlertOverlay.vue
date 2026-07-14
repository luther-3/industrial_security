<template>
  <Transition name="fade">
    <div v-if="visible" class="alert-overlay">
      <span class="alert-text">FALL DETECTED</span>
    </div>
  </Transition>
</template>

<script setup>
defineProps({
  visible: { type: Boolean, default: false },
})
</script>

<style scoped>
.alert-overlay {
  position: absolute;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  background: rgba(245, 108, 108, 0.12);
  border: 3px solid #F56C6C;
  border-radius: 12px;
  padding: 24px 48px;
  pointer-events: none;
  z-index: 10;
}
.alert-text {
  font-size: 36px;
  font-weight: 700;
  color: #F56C6C;
  text-shadow: 0 0 20px rgba(245, 108, 108, 0.5);
  animation: blink 0.8s ease-in-out infinite;
}
@keyframes blink {
  0%, 100% { opacity: 1.0; }
  50% { opacity: 0.3; }
}
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
