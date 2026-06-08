<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="visible"
        class="base-modal-overlay"
        @click.self="onMaskClick"
      >
        <div class="base-modal-card" role="dialog" aria-modal="true" :aria-label="title">
          <div v-if="title || closable" class="base-modal-header">
            <h3 v-if="title" class="base-modal-title">{{ title }}</h3>
            <button
              v-if="closable"
              class="base-modal-close"
              type="button"
              aria-label="关闭"
              @click="requestClose"
            >
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                <path d="M4.5 4.5L13.5 13.5M13.5 4.5L4.5 13.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
              </svg>
            </button>
          </div>
          <div class="base-modal-body">
            <slot />
          </div>
          <div v-if="$slots.footer" class="base-modal-footer">
            <slot name="footer" />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { onMounted, onUnmounted } from "vue";

const props = defineProps({
  visible: { type: Boolean, default: false },
  title: { type: String, default: "" },
  closable: { type: Boolean, default: true },
  maskClosable: { type: Boolean, default: true },
});

const emit = defineEmits(["close"]);

function requestClose() {
  emit("close");
}

function onMaskClick() {
  if (props.maskClosable) {
    requestClose();
  }
}

function onKeydown(e) {
  if (e.key === "Escape" && props.visible) {
    requestClose();
  }
}

onMounted(() => {
  document.addEventListener("keydown", onKeydown);
});

onUnmounted(() => {
  document.removeEventListener("keydown", onKeydown);
});
</script>

<style scoped>
.base-modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: grid;
  place-items: center;
  background: rgba(15, 23, 42, 0.32);
  backdrop-filter: blur(4px);
}

.base-modal-card {
  width: min(480px, 90vw);
  max-height: 85vh;
  overflow-y: auto;
  display: grid;
  gap: var(--space-5);
  padding: 28px;
  border-radius: var(--radius-lg);
  background: var(--bg-surface-strong);
  border: 1px solid var(--border-soft);
  box-shadow: var(--shadow-lg);
}

.base-modal-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
}

.base-modal-title {
  margin: 0;
  font-size: 20px;
  line-height: 1.2;
  letter-spacing: 0;
  color: var(--text-primary);
}

.base-modal-close {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border-radius: var(--radius-sm);
  border: none;
  background: transparent;
  color: var(--text-tertiary);
  cursor: pointer;
  transition:
    background var(--transition-fast),
    color var(--transition-fast);
}

.base-modal-close:hover {
  background: rgba(15, 23, 42, 0.06);
  color: var(--text-primary);
}

.base-modal-body {
  display: grid;
  gap: var(--space-4);
}

.base-modal-footer {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: flex-end;
}

/* Transition: fade + scale */
.modal-enter-active {
  transition: opacity var(--transition-base);
}

.modal-leave-active {
  transition: opacity var(--transition-fast);
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .base-modal-card {
  transition:
    opacity var(--transition-base),
    transform var(--transition-spring);
}

.modal-leave-active .base-modal-card {
  transition:
    opacity var(--transition-fast),
    transform var(--transition-fast);
}

.modal-enter-from .base-modal-card {
  opacity: 0;
  transform: scale(0.95) translateY(8px);
}

.modal-leave-to .base-modal-card {
  opacity: 0;
  transform: scale(0.97) translateY(4px);
}
</style>
