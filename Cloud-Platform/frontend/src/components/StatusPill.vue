<script setup>
import { computed } from "vue";

const props = defineProps({
  label: { type: String, default: "" },
  tone: { type: String, default: "default" }
});

const toneClass = computed(() => {
  if (["success", "warn", "danger"].includes(props.tone)) {
    return props.tone;
  }
  return "";
});
</script>

<template>
  <span class="status-pill" :class="toneClass">{{ label }}</span>
</template>
