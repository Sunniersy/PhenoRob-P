<script setup>
import { toSummaryRows } from "../utils/presenter";

defineProps({
  system: { type: Object, default: null },
  loading: { type: Boolean, default: false }
});
</script>

<template>
  <section class="glass-card" data-reveal-scroll>
    <div class="section-head">
      <div>
        <div class="eyebrow">Bootstrap Check</div>
        <h3>启动自检</h3>
        <p class="page-subtitle">依赖状态与初始化完成度。</p>
      </div>
    </div>
    <p v-if="loading" class="muted-text">正在加载管理数据...</p>
    <div v-else-if="system" class="summary-grid">
      <div class="status-box">
        <strong>初始化</strong>
        <div :class="system.initialization_ok ? 'ok-text' : 'error-text'">
          {{ system.initialization_ok ? "已完成" : "待初始化" }}
        </div>
        <div class="muted-text">needs_initial_admin={{ system.needs_initial_admin ? "true" : "false" }}</div>
      </div>
      <div v-for="(item, key) in system.checks" :key="key" class="status-box">
        <strong>{{ key }}</strong>
        <div :class="item.ok ? 'ok-text' : 'error-text'">{{ item.ok ? "OK" : "FAILED" }}</div>
        <div v-if="toSummaryRows(item.details || {}).length" class="kv-list">
          <div v-for="row in toSummaryRows(item.details || {}, 4)" :key="row.key" class="kv-row">
            <span>{{ row.key }}</span>
            <strong>{{ row.value }}</strong>
          </div>
        </div>
        <div v-else class="muted-text">{{ item.error || "检查通过" }}</div>
      </div>
    </div>
  </section>
</template>
