<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], required: true },
  detail: { type: String, default: "" },
  accent: { type: Boolean, default: false }
});
</script>

<template>
  <article class="metric-card" :class="{ accent }">
    <span class="metric-label">{{ label }}</span>
    <strong class="metric-value">{{ value }}</strong>
    <small v-if="detail" class="metric-detail">{{ detail }}</small>
  </article>
</template>
