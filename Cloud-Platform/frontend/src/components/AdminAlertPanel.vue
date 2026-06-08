<script setup>
import EmptyState from "./EmptyState.vue";
import StatusPill from "./StatusPill.vue";
import { toSummaryRows } from "../utils/presenter";

defineProps({
  alerts: { type: Array, default: () => [] }
});

const emit = defineEmits(["toggle-alert"]);
</script>

<template>
  <section class="glass-card" data-reveal-scroll>
    <div class="section-head">
      <div>
        <div class="eyebrow">Alert Center</div>
        <h3>系统告警</h3>
        <p class="page-subtitle">最近需要关注的异常。</p>
      </div>
    </div>
    <div v-if="alerts.length" class="stack">
      <div v-for="alert in alerts" :key="alert.id" class="status-box">
        <div class="section-head compact">
          <strong>{{ alert.source }}</strong>
          <StatusPill label="alert" tone="danger" />
        </div>
        <div>{{ alert.message }}</div>
        <div class="muted-text">{{ alert.created_at }}</div>
        <div class="toolbar">
          <StatusPill :label="alert.is_acknowledged ? '已确认' : '未确认'" :tone="alert.is_acknowledged ? 'success' : 'warn'" />
          <button class="btn ghost" @click="emit('toggle-alert', alert)">
            {{ alert.is_acknowledged ? "标记未确认" : "确认告警" }}
          </button>
        </div>
        <div v-if="toSummaryRows(alert.payload || {}).length" class="kv-list">
          <div v-for="row in toSummaryRows(alert.payload || {}, 5)" :key="row.key" class="kv-row">
            <span>{{ row.key }}</span>
            <strong>{{ row.value }}</strong>
          </div>
        </div>
      </div>
    </div>
    <EmptyState v-else title="暂无系统告警" compact />
  </section>
</template>
