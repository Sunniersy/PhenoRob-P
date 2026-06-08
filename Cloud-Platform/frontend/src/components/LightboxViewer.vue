<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'

const props = defineProps({
  images: { type: Array, default: () => [] },
  initialIndex: { type: Number, default: 0 },
  visible: { type: Boolean, default: false }
})

const emit = defineEmits(['close', 'update:visible'])

const currentIndex = ref(props.initialIndex)

const currentImage = computed(() => props.images[currentIndex.value])

function close() {
  emit('update:visible', false)
  emit('close')
}

function prev() {
  if (currentIndex.value > 0) {
    currentIndex.value--
  } else {
    currentIndex.value = props.images.length - 1
  }
}

function next() {
  if (currentIndex.value < props.images.length - 1) {
    currentIndex.value++
  } else {
    currentIndex.value = 0
  }
}

function handleKeydown(e) {
  if (!props.visible) return

  switch (e.key) {
    case 'Escape':
      close()
      break
    case 'ArrowLeft':
      prev()
      break
    case 'ArrowRight':
      next()
      break
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})

watch(() => props.initialIndex, (val) => {
  currentIndex.value = val
})
</script>

<template>
  <Teleport to="body">
    <Transition name="lightbox">
      <div
        v-if="visible"
        class="lightbox-overlay"
        @click.self="close"
        role="dialog"
        aria-modal="true"
        aria-label="图片查看器"
      >
        <div class="lightbox-content">
          <img
            v-if="currentImage"
            :src="currentImage.src"
            :alt="currentImage.alt || '图片'"
          />

          <button
            class="lightbox-close"
            @click="close"
            aria-label="关闭"
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>

          <button
            v-if="images.length > 1"
            class="lightbox-nav prev"
            @click="prev"
            aria-label="上一张"
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M15 19l-7-7 7-7" />
            </svg>
          </button>

          <button
            v-if="images.length > 1"
            class="lightbox-nav next"
            @click="next"
            aria-label="下一张"
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 5l7 7-7 7" />
            </svg>
          </button>

          <div v-if="images.length > 1" class="lightbox-counter">
            {{ currentIndex + 1 }} / {{ images.length }}
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.lightbox-enter-active {
  animation: fade-in var(--duration-base) var(--ease-out) both;
}

.lightbox-leave-active {
  animation: fade-in var(--duration-fast) var(--ease-in) reverse both;
}

.lightbox-enter-active .lightbox-content {
  animation: lightbox-in var(--duration-slow) var(--ease-spring) both;
}

.lightbox-leave-active .lightbox-content {
  animation: lightbox-in var(--duration-fast) var(--ease-in) reverse both;
}
</style>
