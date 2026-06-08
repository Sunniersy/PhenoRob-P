<script setup>
defineProps({
  lines: { type: Number, default: 3 }
});
</script>

<template>
  <div class="stack">
    <div v-for="index in lines" :key="index" class="skeleton" :style="{ minHeight: `${54 + index * 10}px` }"></div>
  </div>
</template>
