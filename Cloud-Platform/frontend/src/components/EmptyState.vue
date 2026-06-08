<script setup>
defineProps({
  title: { type: String, required: true },
  description: { type: String, default: "" },
  compact: { type: Boolean, default: false }
});
</script>

<template>
  <div class="empty-state" :class="{ compact }">
    <div class="empty-state-mark" aria-hidden="true"></div>
    <strong>{{ title }}</strong>
    <div v-if="description">{{ description }}</div>
  </div>
</template>
