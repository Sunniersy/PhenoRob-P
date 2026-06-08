<script setup>
const iconPaths = {
  dashboard: "M3.75 4.25A1.5 1.5 0 0 1 5.25 2.75h3.5a1.5 1.5 0 0 1 1.5 1.5v3.5a1.5 1.5 0 0 1-1.5 1.5h-3.5a1.5 1.5 0 0 1-1.5-1.5zm7.5 0a1.5 1.5 0 0 1 1.5-1.5h2a1.5 1.5 0 0 1 1.5 1.5v2a1.5 1.5 0 0 1-1.5 1.5h-2a1.5 1.5 0 0 1-1.5-1.5zm0 5.5a1.5 1.5 0 0 1 1.5-1.5h2a1.5 1.5 0 0 1 1.5 1.5v6a1.5 1.5 0 0 1-1.5 1.5h-2a1.5 1.5 0 0 1-1.5-1.5zm-7.5 3a1.5 1.5 0 0 1 1.5-1.5h3.5a1.5 1.5 0 0 1 1.5 1.5v2a1.5 1.5 0 0 1-1.5 1.5h-3.5a1.5 1.5 0 0 1-1.5-1.5z",
  tasks: "M5 3.5h10A1.5 1.5 0 0 1 16.5 5v10a1.5 1.5 0 0 1-1.5 1.5H5A1.5 1.5 0 0 1 3.5 15V5A1.5 1.5 0 0 1 5 3.5m2-1A1.5 1.5 0 0 1 8.5 4h3A1.5 1.5 0 0 1 13 2.5m-6 5.25h8m-8 3h8m-8 3h5",
  gallery: "M5.25 3.25h9.5a2 2 0 0 1 2 2v9.5a2 2 0 0 1-2 2h-9.5a2 2 0 0 1-2-2v-9.5a2 2 0 0 1 2-2m1.25 9.5 2.25-2.5a1 1 0 0 1 1.5 0l1.5 1.75 2.25-2.75a1 1 0 0 1 1.53 1.28l-2.98 3.64a1 1 0 0 1-1.54.03L8.6 12.12l-1.62 1.8a1 1 0 0 1-1.48-1.34M8 7.5A1.25 1.25 0 1 1 8 5a1.25 1.25 0 0 1 0 2.5",
  robot: "M6.25 3.5h7.5v2h1.25A2.5 2.5 0 0 1 17.5 8v4A2.5 2.5 0 0 1 15 14.5h-.25v1a1 1 0 0 1-2 0v-1h-5.5v1a1 1 0 0 1-2 0v-1H5A2.5 2.5 0 0 1 2.5 12V8A2.5 2.5 0 0 1 5 5.5h1.25zm-.75 5.75A1.25 1.25 0 1 0 5.5 6.75a1.25 1.25 0 0 0 0 2.5m9 0A1.25 1.25 0 1 0 14.5 6.75a1.25 1.25 0 0 0 0 2.5M6 12h8v-2H6z",
  settings: "M8.5 2.75h3l.4 1.85a5.75 5.75 0 0 1 1.24.72l1.8-.67 1.5 2.6-1.4 1.3c.08.4.11.78.11 1.2s-.03.8-.11 1.2l1.4 1.3-1.5 2.6-1.8-.67a5.75 5.75 0 0 1-1.24.72l-.4 1.85h-3l-.4-1.85a5.75 5.75 0 0 1-1.24-.72l-1.8.67-1.5-2.6 1.4-1.3A5.7 5.7 0 0 1 4.25 10c0-.42.03-.8.11-1.2l-1.4-1.3 1.5-2.6 1.8.67c.38-.28.8-.52 1.24-.72zM10 12.75A2.75 2.75 0 1 0 10 7.25a2.75 2.75 0 0 0 0 5.5"
};

defineProps({
  links: { type: Array, default: () => [] },
  platformStats: { type: Array, default: () => [] },
  compact: { type: Boolean, default: false }
});

function iconFor(name) {
  return iconPaths[name] || iconPaths.dashboard;
}
</script>

<template>
  <aside class="app-sidebar" :class="{ compact }">
    <section class="sidebar-brand" data-reveal>
      <div>
        <div class="eyebrow light">Greenhouse Robotics Cloud</div>
        <h2 class="display-title light sidebar-brand-title">温室机器人运营台</h2>
        <div class="sidebar-brand-copy">任务、采集、设备与系统管理</div>
      </div>
      <div class="side-metric-list">
        <div v-for="item in platformStats" :key="item.label" class="side-metric">
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
        </div>
      </div>
      <div class="sidebar-badges">
        <span class="status-pill">MQTT</span>
        <span class="status-pill">MinIO</span>
        <span class="status-pill">Celery</span>
      </div>
    </section>

    <nav class="nav-card" data-reveal>
      <div class="section-head compact">
        <div>
          <div class="eyebrow light">Navigation</div>
          <h3>工作区</h3>
        </div>
      </div>
      <div class="nav-list">
        <router-link v-for="item in links" :key="item.to" :to="item.to" class="nav-link">
          <span class="nav-index" aria-hidden="true">
            <svg class="nav-icon" viewBox="0 0 20 20" fill="none">
              <path :d="iconFor(item.icon)" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </span>
          <div v-if="!compact" class="nav-link-body">
            <div class="nav-title">{{ item.label }}</div>
            <div class="nav-note">{{ item.note }}</div>
          </div>
        </router-link>
      </div>
    </nav>

    <section class="sidebar-card sidebar-footer" data-reveal>
      <div class="eyebrow light">Endpoint</div>
      <strong>访问入口</strong>
      <div class="muted-text">Docker 使用 http://localhost，本机前端使用 http://localhost:5173。</div>
    </section>
  </aside>
</template>
