<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

import CommandPalette from "../components/CommandPalette.vue";
import SidebarNav from "../components/SidebarNav.vue";
import TopCommandBar from "../components/TopCommandBar.vue";
import ThemeToggle from "../components/ThemeToggle.vue";
import { useMotionReveal } from "../composables/useMotionReveal";
import { connectEventSocket, closeEventSocket } from "../services/ws";
import { useAuthStore } from "../stores/auth";
import { useNotificationStore } from "../stores/notifications";

const authStore = useAuthStore();
const notificationStore = useNotificationStore();
const router = useRouter();
const route = useRoute();
const pageRef = ref(null);
const compactSidebar = ref(false);
const commandPaletteVisible = ref(false);

useMotionReveal(pageRef);

const links = [
  { to: "/dashboard", label: "总览", note: "系统概览与依赖状态", index: "01", icon: "dashboard" },
  { to: "/tasks", label: "任务", note: "创建、调度与追踪任务", index: "02", icon: "tasks" },
  { to: "/data", label: "图库", note: "采集资产与正式导入", index: "03", icon: "gallery" },
  { to: "/results", label: "结果", note: "分析结果与报告下载", index: "04", icon: "tasks" },
  { to: "/robots", label: "设备", note: "设备状态与控制命令", index: "05", icon: "robot" },
  { to: "/admin", label: "管理", note: "用户、设备与告警", index: "06", icon: "settings" }
];

const currentSection = computed(() => {
  if (route.path.startsWith("/tasks/") && route.path !== "/tasks") {
    return { label: "任务详情", note: "查看任务状态、资产、结果与时间线。" };
  }
  if (route.meta?.section) {
    return links.find((item) => item.label === route.meta.section) || links[0];
  }
  return links.find((item) => route.path === item.to || route.path.startsWith(`${item.to}/`)) || links[0];
});

const platformStats = computed(() => [
  { label: "账号", value: authStore.user?.username || "--" },
  { label: "链路", value: notificationStore.connected ? "在线" : "离线" },
  { label: "当前页", value: currentSection.value.label }
]);

function syncSidebarMode() {
  compactSidebar.value = window.innerWidth < 1280 && window.innerWidth > 1024;
}

function logout() {
  closeEventSocket();
  authStore.logout();
  router.push("/login");
}

// 监听全局快捷键
function handleGlobalKeydown(event) {
  // Cmd+K 或 Ctrl+K 打开命令面板
  if ((event.metaKey || event.ctrlKey) && event.key === "k") {
    event.preventDefault();
    commandPaletteVisible.value = !commandPaletteVisible.value;
  }
}

onMounted(async () => {
  try {
    if (!authStore.user) {
      await authStore.restore();
    }
  } catch {
    authStore.logout();
    return;
  }

  syncSidebarMode();
  window.addEventListener("resize", syncSidebarMode);
  document.addEventListener("keydown", handleGlobalKeydown);

  connectEventSocket({
    onMessage: (message) => notificationStore.pushEvent(message),
    onOpen: () => notificationStore.markConnected(true),
    onClose: () => notificationStore.markConnected(false),
    onError: () => notificationStore.markConnected(false)
  });
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", syncSidebarMode);
  document.removeEventListener("keydown", handleGlobalKeydown);
});
</script>

<template>
  <div ref="pageRef" class="app-shell">
    <SidebarNav :links="links" :platform-stats="platformStats" :compact="compactSidebar" />

    <main class="app-main">
      <div class="app-main-inner page-grid">
        <div class="app-header">
          <TopCommandBar
            :title="currentSection.label"
            :note="currentSection.note"
            :user="authStore.user"
            :connected="notificationStore.connected"
          >
            <button class="btn secondary" @click="commandPaletteVisible = true">
              <kbd>⌘K</kbd>
            </button>
            <ThemeToggle />
            <router-link class="btn secondary" to="/tasks/create">新建任务</router-link>
            <button class="btn ghost" @click="logout">退出登录</button>
          </TopCommandBar>
        </div>

        <router-view />
      </div>
    </main>

    <!-- 命令面板 -->
    <CommandPalette
      :visible="commandPaletteVisible"
      @close="commandPaletteVisible = false"
    />
  </div>
</template>
