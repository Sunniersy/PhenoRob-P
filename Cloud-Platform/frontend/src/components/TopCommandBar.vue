<script setup>
defineProps({
  title: { type: String, required: true },
  note: { type: String, default: "" },
  user: { type: Object, default: null },
  connected: { type: Boolean, default: false }
});
</script>

<template>
  <header class="command-header" data-reveal>
    <div class="command-header-main">
      <div class="eyebrow">Operations Console</div>
      <h1 class="command-title">{{ title }}</h1>
      <p v-if="note" class="command-copy">{{ note }}</p>
    </div>
    <div class="command-side">
      <div class="command-summary">
        <div class="session-chip">
          <span class="session-label">当前账号</span>
          <strong>{{ user?.username || "--" }}</strong>
          <div class="topbar-meta">
            <span class="status-pill">{{ user?.role || "visitor" }}</span>
            <span class="status-pill" :class="connected ? 'success' : 'danger'">
              {{ connected ? "链路在线" : "链路离线" }}
            </span>
          </div>
        </div>
      </div>
      <div class="command-actions">
        <slot />
      </div>
    </div>
  </header>
</template>
