<template>
  <div :class="['stat-card', isAlert ? 'alert' : 'normal']">
    <div class="label">{{ label }}</div>
    <div class="value">{{ value }}</div>
  </div>
</template>

<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: Number, default: 0 },
  isAlert: { type: Boolean, default: false },
})
</script>

<style scoped>
.stat-card {
  background: #FFFFFF;
  border-radius: 8px;
  border: 1px solid #E4E7ED;
  padding: 20px;
  min-height: 100px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  transition: border-color 0.3s, background-color 0.3s;
}
.stat-card.normal { border-color: #E4E7ED; }
.stat-card.alert {
  border-color: #F56C6C;
  background-color: #FEF0F0;
}
.label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}
.normal .value { color: #67C23A; }
.alert .value { color: #F56C6C; }
.value {
  font-size: 48px;
  font-weight: 700;
  font-family: 'SF Mono', 'Menlo', 'Consolas', monospace;
  font-variant-numeric: tabular-nums;
}
</style>
