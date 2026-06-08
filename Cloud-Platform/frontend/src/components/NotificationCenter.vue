<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue";
import { useNotificationStore } from "../stores/notifications";

defineProps({
  visible: { type: Boolean, default: false }
});

const emit = defineEmits(["close"]);

const notificationStore = useNotificationStore();
const filter = ref("all"); // all, unread, read

// 通知列表
const notifications = computed(() => {
  let items = notificationStore.recent || [];

  // 过滤
  if (filter.value === "unread") {
    items = items.filter((n) => !n.read);
  } else if (filter.value === "read") {
    items = items.filter((n) => n.read);
  }

  return items;
});

// 未读数量
const unreadCount = computed(() => {
  return (notificationStore.recent || []).filter((n) => !n.read).length;
});

// 标记为已读
function markAsRead(id) {
  notificationStore.markAsRead(id);
}

// 标记所有为已读
function markAllAsRead() {
  notificationStore.markAllAsRead();
}

// 清除所有通知
function clearAll() {
  notificationStore.clearAll();
}

// 关闭
function close() {
  emit("close");
}

// 获取通知图标
function getNotificationIcon(type) {
  switch (type) {
    case "task.updated":
      return "tasks";
    case "robot.state":
      return "robot";
    case "analysis.complete":
      return "results";
    case "alert":
      return "alert";
    default:
      return "info";
  }
}

// 获取通知颜色
function getNotificationColor(type) {
  switch (type) {
    case "task.updated":
      return "var(--brand)";
    case "robot.state":
      return "var(--info)";
    case "analysis.complete":
      return "var(--success)";
    case "alert":
      return "var(--warning)";
    default:
      return "var(--text-secondary)";
  }
}

// 格式化时间
function formatTime(timestamp) {
  if (!timestamp) return "";
  const date = new Date(timestamp);
  const now = new Date();
  const diff = now - date;

  if (diff < 60000) return "刚刚";
  if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`;
  return date.toLocaleDateString();
}

// 监听全局快捷键
function handleKeydown(event) {
  if (event.key === "Escape") {
    close();
  }
}

onMounted(() => {
  document.addEventListener("keydown", handleKeydown);
});

onUnmounted(() => {
  document.removeEventListener("keydown", handleKeydown);
});
</script>

<template>
  <Teleport to="body">
    <Transition name="notification-center">
      <div
        v-if="visible"
        class="notification-center-overlay"
        @click.self="close"
        role="dialog"
        aria-modal="true"
        aria-label="通知中心"
      >
        <div class="notification-center">
          <!-- 头部 -->
          <div class="notification-center-header">
            <div class="notification-center-title">
              <h3>通知中心</h3>
              <span v-if="unreadCount" class="notification-center-badge">
                {{ unreadCount }}
              </span>
            </div>
            <div class="notification-center-actions">
              <button
                class="btn ghost btn-sm"
                @click="markAllAsRead"
                :disabled="!unreadCount"
              >
                全部已读
              </button>
              <button
                class="btn ghost btn-sm"
                @click="clearAll"
                :disabled="!notifications.length"
              >
                清除所有
              </button>
              <button
                class="btn ghost btn-sm"
                @click="close"
                aria-label="关闭"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M18 6L6 18M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          <!-- 筛选 -->
          <div class="notification-center-filters">
            <button
              class="chip"
              :class="{ active: filter === 'all' }"
              @click="filter = 'all'"
            >
              全部
            </button>
            <button
              class="chip"
              :class="{ active: filter === 'unread' }"
              @click="filter = 'unread'"
            >
              未读
            </button>
            <button
              class="chip"
              :class="{ active: filter === 'read' }"
              @click="filter = 'read'"
            >
              已读
            </button>
          </div>

          <!-- 通知列表 -->
          <div class="notification-center-list">
            <div
              v-for="notification in notifications"
              :key="notification.id"
              class="notification-item"
              :class="{ unread: !notification.read }"
              @click="markAsRead(notification.id)"
            >
              <div
                class="notification-item-icon"
                :style="{ color: getNotificationColor(notification.event) }"
              >
                <!-- Tasks -->
                <svg v-if="getNotificationIcon(notification.event) === 'tasks'" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
                <!-- Robot -->
                <svg v-else-if="getNotificationIcon(notification.event) === 'robot'" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="2" y="7" width="20" height="14" rx="2" ry="2" />
                  <path d="M16 21V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v16" />
                </svg>
                <!-- Results -->
                <svg v-else-if="getNotificationIcon(notification.event) === 'results'" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
                  <polyline points="14 2 14 8 20 8" />
                </svg>
                <!-- Alert -->
                <svg v-else-if="getNotificationIcon(notification.event) === 'alert'" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
                  <line x1="12" y1="9" x2="12" y2="13" />
                  <line x1="12" y1="17" x2="12.01" y2="17" />
                </svg>
                <!-- Info -->
                <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="10" />
                  <line x1="12" y1="16" x2="12" y2="12" />
                  <line x1="12" y1="8" x2="12.01" y2="8" />
                </svg>
              </div>

              <div class="notification-item-content">
                <div class="notification-item-title">
                  {{ notification.payload?.message || notification.event }}
                </div>
                <div class="notification-item-meta">
                  <span class="notification-item-time">
                    {{ formatTime(notification.timestamp) }}
                  </span>
                </div>
              </div>

              <div v-if="!notification.read" class="notification-item-dot"></div>
            </div>

            <!-- 空状态 -->
            <div
              v-if="!notifications.length"
              class="notification-empty"
            >
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9" />
                <path d="M13.73 21a2 2 0 01-3.46 0" />
              </svg>
              <p>{{ filter === 'unread' ? '没有未读通知' : '没有通知' }}</p>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.notification-center-overlay {
  position: fixed;
  inset: 0;
  z-index: 1500;
  display: flex;
  align-items: flex-start;
  justify-content: flex-end;
  padding: var(--space-6);
  background: rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(4px);
}

.notification-center {
  width: min(400px, 100%);
  max-height: calc(100vh - 120px);
  display: flex;
  flex-direction: column;
  background: var(--bg-surface-solid);
  border: 1px solid var(--border-medium);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-lg);
  overflow: hidden;
}

.notification-center-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-4);
  border-bottom: 1px solid var(--border-soft);
}

.notification-center-title {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.notification-center-title h3 {
  margin: 0;
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
}

.notification-center-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 var(--space-1);
  background: var(--danger);
  color: #ffffff;
  font-size: var(--text-xs);
  font-weight: var(--font-bold);
  border-radius: var(--radius-pill);
}

.notification-center-actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.notification-center-filters {
  display: flex;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  border-bottom: 1px solid var(--border-soft);
}

.notification-center-list {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-2);
}

.notification-item {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background var(--duration-fast) var(--ease-default);
}

.notification-item:hover {
  background: var(--gray-100);
}

.notification-item.unread {
  background: var(--brand-subtle);
}

.notification-item.unread:hover {
  background: var(--brand-muted);
}

.notification-item-icon {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background: var(--bg-surface-muted);
  border-radius: var(--radius-sm);
}

.notification-item-content {
  flex: 1;
  min-width: 0;
}

.notification-item-title {
  font-size: var(--text-sm);
  color: var(--text-primary);
  line-height: var(--leading-normal);
}

.notification-item-meta {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-top: var(--space-1);
}

.notification-item-time {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.notification-item-dot {
  flex-shrink: 0;
  width: 8px;
  height: 8px;
  background: var(--brand);
  border-radius: 50%;
  margin-top: var(--space-2);
}

.notification-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-4);
  padding: var(--space-8);
  color: var(--text-tertiary);
}

.notification-empty p {
  margin: 0;
  font-size: var(--text-sm);
}

/* 动画 */
.notification-center-enter-active {
  animation: fade-in var(--duration-base) var(--ease-out) both;
}

.notification-center-leave-active {
  animation: fade-in var(--duration-fast) var(--ease-in) reverse both;
}

.notification-center-enter-active .notification-center {
  animation: slide-in-right var(--duration-base) var(--ease-out) both;
}

.notification-center-leave-active .notification-center {
  animation: slide-in-right var(--duration-fast) var(--ease-in) reverse both;
}

@keyframes slide-in-right {
  from {
    opacity: 0;
    transform: translateX(20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

/* 响应式 */
@media (max-width: 767px) {
  .notification-center-overlay {
    padding: var(--space-4);
  }

  .notification-center {
    max-height: calc(100vh - 80px);
  }
}
</style>
