<script setup>
import EmptyState from "./EmptyState.vue";
import { formatValue } from "../utils/presenter";

defineProps({
  items: { type: Array, default: () => [] },
  emptyTitle: { type: String, default: "暂无时间线事件" }
});
</script>

<template>
  <EmptyState v-if="!items.length" :title="emptyTitle" compact />
  <div v-else class="timeline">
    <div v-for="item in items" :key="item.id || `${item.created_at}-${item.event_type}`" class="timeline-item">
      <div class="timeline-dot"></div>
      <div class="timeline-body">
        <strong>{{ item.event_type || item.event }}</strong>
        <div class="muted-text">{{ item.created_at || item.timestamp }}</div>
        <div v-if="item.rows?.length" class="kv-list">
          <div v-for="row in item.rows" :key="row.key" class="kv-row">
            <span>{{ row.key }}</span>
            <strong>{{ row.value }}</strong>
          </div>
        </div>
        <div v-else class="muted-text">详情：{{ formatValue(item.payload) }}</div>
      </div>
    </div>
  </div>
</template>
