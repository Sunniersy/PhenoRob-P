<template>
  <nav v-if="items.length > 1" class="breadcrumb" aria-label="面包屑导航">
    <template v-for="(item, index) in items" :key="index">
      <span v-if="index > 0" class="breadcrumb-sep">/</span>
      <router-link v-if="item.to && index < items.length - 1" :to="item.to" class="breadcrumb-link">
        {{ item.label }}
      </router-link>
      <span v-else class="breadcrumb-current">{{ item.label }}</span>
    </template>
  </nav>
</template>

<script setup>
defineProps({
  items: { type: Array, default: () => [] },
});
</script>

<style scoped>
.breadcrumb {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.85rem;
  color: var(--text-secondary, #888);
  margin-bottom: 16px;
}
.breadcrumb-link {
  color: var(--color-primary, #6366f1);
  text-decoration: none;
}
.breadcrumb-link:hover {
  text-decoration: underline;
}
.breadcrumb-current {
  color: var(--text-primary, #333);
}
</style>
