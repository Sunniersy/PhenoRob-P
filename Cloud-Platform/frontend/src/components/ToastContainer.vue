<script setup>
import { ref } from 'vue'

const toasts = ref([])
let nextId = 0

function addToast({ type = 'info', title, message, duration = 3000 }) {
  const id = nextId++
  const toast = { id, type, title, message, exiting: false }
  toasts.value.push(toast)

  if (duration > 0) {
    setTimeout(() => removeToast(id), duration)
  }

  return id
}

function removeToast(id) {
  const index = toasts.value.findIndex(t => t.id === id)
  if (index === -1) return

  toasts.value[index].exiting = true
  setTimeout(() => {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }, 220)
}

function success(title, message) {
  return addToast({ type: 'success', title, message })
}

function error(title, message) {
  return addToast({ type: 'error', title, message, duration: 5000 })
}

function warning(title, message) {
  return addToast({ type: 'warning', title, message })
}

function info(title, message) {
  return addToast({ type: 'info', title, message })
}

// 暴露给全局使用
defineExpose({ addToast, removeToast, success, error, warning, info })

const iconPaths = {
  success: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
  error: 'M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z',
  warning: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4.5c-.77-.833-2.694-.833-3.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z',
  info: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z'
}

const iconColors = {
  success: 'var(--success-500)',
  error: 'var(--danger-500)',
  warning: 'var(--warning-500)',
  info: 'var(--info-500)'
}
</script>

<template>
  <div class="toast-container" role="region" aria-label="通知">
    <div
      v-for="toast in toasts"
      :key="toast.id"
      :class="['toast', toast.type, { 'toast-exit': toast.exiting }]"
      role="alert"
    >
      <svg
        class="toast-icon"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
        :style="{ color: iconColors[toast.type] }"
      >
        <path :d="iconPaths[toast.type]" />
      </svg>
      <div class="toast-content">
        <div v-if="toast.title" class="toast-title">{{ toast.title }}</div>
        <div v-if="toast.message" class="toast-message">{{ toast.message }}</div>
      </div>
      <button
        class="toast-close"
        @click="removeToast(toast.id)"
        aria-label="关闭"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M18 6L6 18M6 6l12 12" />
        </svg>
      </button>
    </div>
  </div>
</template>
