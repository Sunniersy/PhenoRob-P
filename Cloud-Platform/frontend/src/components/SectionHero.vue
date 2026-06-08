<script setup>
defineProps({
  eyebrow: { type: String, default: "" },
  title: { type: String, required: true },
  subtitle: { type: String, default: "" },
  split: { type: Boolean, default: false }
});
</script>

<template>
  <section class="glass-card hero-card section-hero" :class="{ 'hero-split': split }">
    <div class="section-hero-main">
      <div v-if="eyebrow" class="eyebrow">{{ eyebrow }}</div>
      <h1 class="page-title">{{ title }}</h1>
      <p v-if="subtitle" class="page-subtitle">{{ subtitle }}</p>
      <div v-if="$slots.actions" class="section-hero-actions">
        <slot name="actions" />
      </div>
    </div>
    <div v-if="$slots.aside" class="section-hero-aside">
      <slot name="aside" />
    </div>
  </section>
</template>
