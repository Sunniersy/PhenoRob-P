<script setup>
import { computed } from "vue";

const props = defineProps({
  files: { type: Array, default: () => [] },
  currentIndex: { type: Number, default: 0 },
  currentProgress: { type: Number, default: 0 },
  visible: { type: Boolean, default: false }
});

const totalFiles = computed(() => props.files.length);
const currentFileName = computed(() => props.files[props.currentIndex]?.name || "");
const overallPercent = computed(() => {
  if (!totalFiles.value) return 0;
  const fileWeight = 100 / totalFiles.value;
  return Math.min(100, Math.round(props.currentIndex * fileWeight + (props.currentProgress / 100) * fileWeight));
});
</script>

<template>
  <Transition name="upload-slide">
    <div v-if="visible" class="upload-progress">
      <div class="upload-progress-header">
        <span class="upload-progress-label">正在上传</span>
        <span class="upload-progress-count">{{ currentIndex + 1 }} / {{ totalFiles }}</span>
      </div>
      <div class="upload-progress-file">{{ currentFileName }}</div>
      <div class="upload-progress-bar-track">
        <div class="upload-progress-bar-fill" :style="{ width: overallPercent + '%' }"></div>
      </div>
      <div class="upload-progress-percent">{{ overallPercent }}%</div>
    </div>
  </Transition>
</template>

<style scoped>
.upload-progress {
  display: grid;
  gap: 8px;
  padding: 16px 18px;
  border-radius: var(--radius-md);
  background: var(--bg-surface-accent);
  border: 1px solid rgba(16, 163, 127, 0.22);
  box-shadow: var(--shadow-sm);
}

.upload-progress-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.upload-progress-label {
  color: var(--brand);
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0;
}

.upload-progress-count {
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 600;
}

.upload-progress-file {
  color: var(--text-primary);
  font-size: 13px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.upload-progress-bar-track {
  height: 6px;
  border-radius: var(--radius-pill);
  background: var(--bg-surface-muted);
  overflow: hidden;
}

.upload-progress-bar-fill {
  height: 100%;
  border-radius: var(--radius-pill);
  background: linear-gradient(90deg, var(--brand), var(--accent));
  transition: width 300ms cubic-bezier(0.22, 1, 0.36, 1);
}

.upload-progress-percent {
  color: var(--text-tertiary);
  font-size: 12px;
  font-weight: 600;
  text-align: right;
}

.upload-slide-enter-active {
  transition: opacity 220ms ease, transform 220ms ease;
}

.upload-slide-leave-active {
  transition: opacity 160ms ease, transform 160ms ease;
}

.upload-slide-enter-from {
  opacity: 0;
  transform: translateY(-8px);
}

.upload-slide-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
