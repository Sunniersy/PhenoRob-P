<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from "vue";
import { useRouter } from "vue-router";

const props = defineProps({
  visible: { type: Boolean, default: false }
});

const emit = defineEmits(["close"]);

const router = useRouter();
const searchQuery = ref("");
const selectedIndex = ref(0);
const searchInput = ref(null);

// 命令列表
const commands = [
  {
    id: "dashboard",
    label: "总览",
    description: "系统概览与依赖状态",
    icon: "dashboard",
    action: () => router.push("/dashboard"),
    keywords: ["总览", "dashboard", "首页", "home"]
  },
  {
    id: "tasks",
    label: "任务",
    description: "创建、调度与追踪任务",
    icon: "tasks",
    action: () => router.push("/tasks"),
    keywords: ["任务", "tasks", "创建", "调度"]
  },
  {
    id: "create-task",
    label: "创建任务",
    description: "新建采集任务",
    icon: "add",
    action: () => router.push("/tasks/create"),
    keywords: ["创建", "新建", "create", "add"]
  },
  {
    id: "gallery",
    label: "图库",
    description: "采集资产与正式导入",
    icon: "gallery",
    action: () => router.push("/data"),
    keywords: ["图库", "gallery", "图片", "资产"]
  },
  {
    id: "results",
    label: "结果",
    description: "分析结果与报告下载",
    icon: "results",
    action: () => router.push("/results"),
    keywords: ["结果", "results", "分析", "报告"]
  },
  {
    id: "robots",
    label: "设备",
    description: "设备状态与控制命令",
    icon: "robot",
    action: () => router.push("/robots"),
    keywords: ["设备", "robots", "机器人", "控制"]
  },
  {
    id: "admin",
    label: "管理",
    description: "用户、设备与告警",
    icon: "settings",
    action: () => router.push("/admin"),
    keywords: ["管理", "admin", "用户", "设置"]
  },
  {
    id: "theme",
    label: "切换主题",
    description: "在亮色和暗色主题之间切换",
    icon: "theme",
    action: () => {
      const html = document.documentElement;
      const current = html.getAttribute("data-theme");
      html.setAttribute("data-theme", current === "dark" ? "light" : "dark");
      localStorage.setItem("phenobot-theme", current === "dark" ? "light" : "dark");
    },
    keywords: ["主题", "theme", "暗色", "深色", "亮色", "浅色"]
  },
  {
    id: "refresh",
    label: "刷新页面",
    description: "重新加载当前页面数据",
    icon: "refresh",
    action: () => window.location.reload(),
    keywords: ["刷新", "refresh", "重新加载"]
  },
  {
    id: "logout",
    label: "退出登录",
    description: "退出当前账号",
    icon: "logout",
    action: () => {
      localStorage.removeItem("token");
      localStorage.removeItem("refresh_token");
      router.push("/login");
    },
    keywords: ["退出", "logout", "登出"]
  }
];

// 过滤命令
const filteredCommands = computed(() => {
  if (!searchQuery.value) return commands;

  const query = searchQuery.value.toLowerCase();
  return commands.filter((cmd) => {
    return (
      cmd.label.toLowerCase().includes(query) ||
      cmd.description.toLowerCase().includes(query) ||
      cmd.keywords.some((kw) => kw.includes(query))
    );
  });
});

// 选择命令
function selectCommand(command) {
  command.action();
  close();
}

// 关闭
function close() {
  searchQuery.value = "";
  selectedIndex.value = 0;
  emit("close");
}

// 键盘导航
function handleKeydown(event) {
  switch (event.key) {
    case "ArrowDown":
      event.preventDefault();
      selectedIndex.value = Math.min(selectedIndex.value + 1, filteredCommands.value.length - 1);
      break;
    case "ArrowUp":
      event.preventDefault();
      selectedIndex.value = Math.max(selectedIndex.value - 1, 0);
      break;
    case "Enter":
      event.preventDefault();
      if (filteredCommands.value[selectedIndex.value]) {
        selectCommand(filteredCommands.value[selectedIndex.value]);
      }
      break;
    case "Escape":
      event.preventDefault();
      close();
      break;
  }
}

// 监听全局快捷键
function handleGlobalKeydown(event) {
  // Cmd+K 或 Ctrl+K 打开命令面板
  if ((event.metaKey || event.ctrlKey) && event.key === "k") {
    event.preventDefault();
    if (!props.visible) {
      // 打开命令面板
      emit("close"); // 触发父组件切换
    }
  }
}

onMounted(() => {
  document.addEventListener("keydown", handleGlobalKeydown);
});

onUnmounted(() => {
  document.removeEventListener("keydown", handleGlobalKeydown);
});

// 当面板打开时，聚焦搜索框
watch(() => props.visible, (newVal) => {
  if (newVal) {
    nextTick(() => {
      searchInput.value?.focus();
    });
  }
});
</script>

<template>
  <Teleport to="body">
    <Transition name="command-palette">
      <div
        v-if="visible"
        class="command-palette-overlay"
        @click.self="close"
        role="dialog"
        aria-modal="true"
        aria-label="命令面板"
      >
        <div class="command-palette" @keydown="handleKeydown">
          <!-- 搜索框 -->
          <div class="command-palette-search">
            <svg
              class="command-palette-icon"
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <circle cx="11" cy="11" r="8" />
              <path d="M21 21l-4.35-4.35" />
            </svg>
            <input
              ref="searchInput"
              v-model="searchQuery"
              class="command-palette-input"
              placeholder="搜索命令或页面..."
              autocomplete="off"
              spellcheck="false"
            />
            <kbd class="command-palette-kbd">ESC</kbd>
          </div>

          <!-- 命令列表 -->
          <div class="command-palette-list">
            <div
              v-for="(command, index) in filteredCommands"
              :key="command.id"
              class="command-palette-item"
              :class="{ active: index === selectedIndex }"
              @click="selectCommand(command)"
              @mouseenter="selectedIndex = index"
            >
              <div class="command-palette-item-icon">
                <!-- Dashboard -->
                <svg v-if="command.icon === 'dashboard'" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="3" y="3" width="7" height="7" />
                  <rect x="14" y="3" width="7" height="7" />
                  <rect x="14" y="14" width="7" height="7" />
                  <rect x="3" y="14" width="7" height="7" />
                </svg>
                <!-- Tasks -->
                <svg v-else-if="command.icon === 'tasks'" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
                <!-- Add -->
                <svg v-else-if="command.icon === 'add'" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="10" />
                  <path d="M12 8v8M8 12h8" />
                </svg>
                <!-- Gallery -->
                <svg v-else-if="command.icon === 'gallery'" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                  <circle cx="8.5" cy="8.5" r="1.5" />
                  <polyline points="21 15 16 10 5 21" />
                </svg>
                <!-- Results -->
                <svg v-else-if="command.icon === 'results'" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
                  <polyline points="14 2 14 8 20 8" />
                  <line x1="16" y1="13" x2="8" y2="13" />
                  <line x1="16" y1="17" x2="8" y2="17" />
                </svg>
                <!-- Robot -->
                <svg v-else-if="command.icon === 'robot'" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="2" y="7" width="20" height="14" rx="2" ry="2" />
                  <path d="M16 21V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v16" />
                </svg>
                <!-- Settings -->
                <svg v-else-if="command.icon === 'settings'" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="3" />
                  <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z" />
                </svg>
                <!-- Theme -->
                <svg v-else-if="command.icon === 'theme'" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="5" />
                  <line x1="12" y1="1" x2="12" y2="3" />
                  <line x1="12" y1="21" x2="12" y2="23" />
                  <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
                  <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
                  <line x1="1" y1="12" x2="3" y2="12" />
                  <line x1="21" y1="12" x2="23" y2="12" />
                  <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
                  <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
                </svg>
                <!-- Refresh -->
                <svg v-else-if="command.icon === 'refresh'" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="23 4 23 10 17 10" />
                  <polyline points="1 20 1 14 7 14" />
                  <path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15" />
                </svg>
                <!-- Logout -->
                <svg v-else-if="command.icon === 'logout'" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4" />
                  <polyline points="16 17 21 12 16 7" />
                  <line x1="21" y1="12" x2="9" y2="12" />
                </svg>
              </div>
              <div class="command-palette-item-content">
                <div class="command-palette-item-label">{{ command.label }}</div>
                <div class="command-palette-item-description">{{ command.description }}</div>
              </div>
              <kbd v-if="index === selectedIndex" class="command-palette-kbd">↵</kbd>
            </div>

            <!-- 空状态 -->
            <div
              v-if="!filteredCommands.length"
              class="command-palette-empty"
            >
              没有找到匹配的命令
            </div>
          </div>

          <!-- 底部提示 -->
          <div class="command-palette-footer">
            <div class="command-palette-hints">
              <span><kbd>↑↓</kbd> 导航</span>
              <span><kbd>↵</kbd> 选择</span>
              <span><kbd>ESC</kbd> 关闭</span>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.command-palette-overlay {
  position: fixed;
  inset: 0;
  z-index: 2000;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 20vh;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
}

.command-palette {
  width: min(560px, 90vw);
  max-height: 400px;
  display: flex;
  flex-direction: column;
  background: var(--bg-surface-solid);
  border: 1px solid var(--border-medium);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-lg);
  overflow: hidden;
}

.command-palette-search {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4);
  border-bottom: 1px solid var(--border-soft);
}

.command-palette-icon {
  flex-shrink: 0;
  color: var(--text-tertiary);
}

.command-palette-input {
  flex: 1;
  border: none;
  background: transparent;
  font-size: var(--text-lg);
  color: var(--text-primary);
  outline: none;
}

.command-palette-input::placeholder {
  color: var(--text-quiet);
}

.command-palette-kbd {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 24px;
  height: 24px;
  padding: 0 var(--space-2);
  background: var(--gray-100);
  border: 1px solid var(--border-soft);
  border-radius: var(--radius-xs);
  font-size: var(--text-xs);
  font-family: var(--font-mono);
  color: var(--text-tertiary);
}

.command-palette-list {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-2);
}

.command-palette-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background var(--duration-fast) var(--ease-default);
}

.command-palette-item:hover,
.command-palette-item.active {
  background: var(--gray-100);
}

.command-palette-item-icon {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: var(--bg-surface-muted);
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
}

.command-palette-item-content {
  flex: 1;
  min-width: 0;
}

.command-palette-item-label {
  font-size: var(--text-base);
  font-weight: var(--font-medium);
  color: var(--text-primary);
}

.command-palette-item-description {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
  margin-top: 2px;
}

.command-palette-empty {
  padding: var(--space-8) var(--space-4);
  text-align: center;
  color: var(--text-tertiary);
  font-size: var(--text-sm);
}

.command-palette-footer {
  padding: var(--space-3) var(--space-4);
  border-top: 1px solid var(--border-soft);
  background: var(--bg-surface-muted);
}

.command-palette-hints {
  display: flex;
  gap: var(--space-4);
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.command-palette-hints kbd {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 var(--space-1);
  background: var(--bg-surface-solid);
  border: 1px solid var(--border-soft);
  border-radius: var(--radius-xs);
  font-size: 10px;
  font-family: var(--font-mono);
  margin-right: var(--space-1);
}

/* 动画 */
.command-palette-enter-active {
  animation: fade-in var(--duration-base) var(--ease-out) both;
}

.command-palette-leave-active {
  animation: fade-in var(--duration-fast) var(--ease-in) reverse both;
}

.command-palette-enter-active .command-palette {
  animation: scale-in var(--duration-slow) var(--ease-spring) both;
}

.command-palette-leave-active .command-palette {
  animation: scale-in var(--duration-fast) var(--ease-in) reverse both;
}

/* 响应式 */
@media (max-width: 767px) {
  .command-palette-overlay {
    padding-top: 10vh;
  }

  .command-palette {
    max-height: 60vh;
  }
}
</style>
