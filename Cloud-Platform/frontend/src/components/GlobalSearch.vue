<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from "vue";
import { useRouter } from "vue-router";
import { tasks as tasksApi, robots as robotsApi, assets as assetsApi } from "../api";

const props = defineProps({
  visible: { type: Boolean, default: false }
});

const emit = defineEmits(["close"]);

const router = useRouter();
const searchQuery = ref("");
const searchInput = ref(null);
const loading = ref(false);
const results = ref({
  tasks: [],
  robots: [],
  assets: []
});

// 搜索结果总数
const totalResults = computed(() => {
  return results.value.tasks.length + results.value.robots.length + results.value.assets.length;
});

// 防抖搜索
let searchTimeout = null;

watch(searchQuery, (newQuery) => {
  if (searchTimeout) clearTimeout(searchTimeout);

  if (!newQuery.trim()) {
    results.value = { tasks: [], robots: [], assets: [] };
    return;
  }

  searchTimeout = setTimeout(() => {
    performSearch(newQuery);
  }, 300);
});

// 执行搜索
async function performSearch(query) {
  loading.value = true;
  try {
    const [tasksResult, robotsResult, assetsResult] = await Promise.allSettled([
      tasksApi.list({ q: query, page: 1, page_size: 5 }),
      robotsApi.list({ page: 1, page_size: 5 }),
      assetsApi.list({ q: query, page: 1, page_size: 5 })
    ]);

    results.value = {
      tasks: tasksResult.status === "fulfilled" ? tasksResult.value.items : [],
      robots: robotsResult.status === "fulfilled" ? robotsResult.value.items : [],
      assets: assetsResult.status === "fulfilled" ? assetsResult.value.items : []
    };
  } catch (err) {
    console.error("Search error:", err);
  } finally {
    loading.value = false;
  }
}

// 导航到结果
function navigateTo(type, item) {
  close();

  switch (type) {
    case "task":
      router.push(`/tasks/${item.id}`);
      break;
    case "robot":
      router.push(`/robots`);
      break;
    case "asset":
      router.push(`/data`);
      break;
  }
}

// 关闭
function close() {
  searchQuery.value = "";
  results.value = { tasks: [], robots: [], assets: [] };
  emit("close");
}

// 键盘导航
function handleKeydown(event) {
  if (event.key === "Escape") {
    close();
  }
}

onMounted(() => {
  document.addEventListener("keydown", handleKeydown);
  if (props.visible) {
    nextTick(() => {
      searchInput.value?.focus();
    });
  }
});

onUnmounted(() => {
  document.removeEventListener("keydown", handleKeydown);
  if (searchTimeout) clearTimeout(searchTimeout);
});

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
    <Transition name="global-search">
      <div
        v-if="visible"
        class="global-search-overlay"
        @click.self="close"
        role="dialog"
        aria-modal="true"
        aria-label="全局搜索"
      >
        <div class="global-search">
          <!-- 搜索框 -->
          <div class="global-search-header">
            <svg
              class="global-search-icon"
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
              class="global-search-input"
              placeholder="搜索任务、机器人、资产..."
              autocomplete="off"
              spellcheck="false"
            />
            <kbd class="global-search-kbd">ESC</kbd>
          </div>

          <!-- 搜索结果 -->
          <div class="global-search-results">
            <!-- 加载状态 -->
            <div v-if="loading" class="global-search-loading">
              <div class="global-search-loading-spinner"></div>
              <span>搜索中...</span>
            </div>

            <!-- 无搜索词 -->
            <div v-else-if="!searchQuery.trim()" class="global-search-empty">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <circle cx="11" cy="11" r="8" />
                <path d="M21 21l-4.35-4.35" />
              </svg>
              <p>输入关键词搜索任务、机器人或资产</p>
            </div>

            <!-- 无结果 -->
            <div v-else-if="!totalResults" class="global-search-empty">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <circle cx="11" cy="11" r="8" />
                <path d="M21 21l-4.35-4.35" />
                <line x1="8" y1="11" x2="14" y2="11" />
              </svg>
              <p>没有找到匹配的结果</p>
            </div>

            <!-- 搜索结果 -->
            <template v-else>
              <!-- 任务结果 -->
              <div v-if="results.tasks.length" class="global-search-section">
                <div class="global-search-section-title">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                  </svg>
                  <span>任务</span>
                </div>
                <div
                  v-for="task in results.tasks"
                  :key="task.id"
                  class="global-search-item"
                  @click="navigateTo('task', task)"
                >
                  <div class="global-search-item-content">
                    <div class="global-search-item-title">{{ task.name }}</div>
                    <div class="global-search-item-meta">
                      <span class="global-search-item-type">{{ task.task_type }}</span>
                      <span class="global-search-item-status">{{ task.status }}</span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 机器人结果 -->
              <div v-if="results.robots.length" class="global-search-section">
                <div class="global-search-section-title">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="2" y="7" width="20" height="14" rx="2" ry="2" />
                    <path d="M16 21V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v16" />
                  </svg>
                  <span>机器人</span>
                </div>
                <div
                  v-for="robot in results.robots"
                  :key="robot.id"
                  class="global-search-item"
                  @click="navigateTo('robot', robot)"
                >
                  <div class="global-search-item-content">
                    <div class="global-search-item-title">{{ robot.name }}</div>
                    <div class="global-search-item-meta">
                      <span class="global-search-item-type">{{ robot.robot_code }}</span>
                      <span class="global-search-item-status">{{ robot.status }}</span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 资产结果 -->
              <div v-if="results.assets.length" class="global-search-section">
                <div class="global-search-section-title">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                    <circle cx="8.5" cy="8.5" r="1.5" />
                    <polyline points="21 15 16 10 5 21" />
                  </svg>
                  <span>资产</span>
                </div>
                <div
                  v-for="asset in results.assets"
                  :key="asset.id"
                  class="global-search-item"
                  @click="navigateTo('asset', asset)"
                >
                  <div class="global-search-item-content">
                    <div class="global-search-item-title">{{ asset.file_name }}</div>
                    <div class="global-search-item-meta">
                      <span class="global-search-item-type">{{ asset.asset_type }}</span>
                      <span class="global-search-item-status">{{ asset.created_at }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </template>
          </div>

          <!-- 底部提示 -->
          <div class="global-search-footer">
            <div class="global-search-hints">
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
.global-search-overlay {
  position: fixed;
  inset: 0;
  z-index: 2000;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 15vh;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
}

.global-search {
  width: min(640px, 90vw);
  max-height: 500px;
  display: flex;
  flex-direction: column;
  background: var(--bg-surface-solid);
  border: 1px solid var(--border-medium);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-lg);
  overflow: hidden;
}

.global-search-header {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4);
  border-bottom: 1px solid var(--border-soft);
}

.global-search-icon {
  flex-shrink: 0;
  color: var(--text-tertiary);
}

.global-search-input {
  flex: 1;
  border: none;
  background: transparent;
  font-size: var(--text-lg);
  color: var(--text-primary);
  outline: none;
}

.global-search-input::placeholder {
  color: var(--text-quiet);
}

.global-search-kbd {
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

.global-search-results {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-2);
}

.global-search-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  padding: var(--space-8);
  color: var(--text-tertiary);
}

.global-search-loading-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid var(--border-soft);
  border-top-color: var(--brand);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.global-search-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-4);
  padding: var(--space-8);
  color: var(--text-tertiary);
}

.global-search-empty p {
  margin: 0;
  font-size: var(--text-sm);
}

.global-search-section {
  margin-bottom: var(--space-4);
}

.global-search-section-title {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  font-size: var(--text-xs);
  font-weight: var(--font-bold);
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: var(--tracking-wide);
}

.global-search-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background var(--duration-fast) var(--ease-default);
}

.global-search-item:hover {
  background: var(--gray-100);
}

.global-search-item-content {
  flex: 1;
  min-width: 0;
}

.global-search-item-title {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.global-search-item-meta {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-top: var(--space-1);
}

.global-search-item-type,
.global-search-item-status {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.global-search-footer {
  padding: var(--space-3) var(--space-4);
  border-top: 1px solid var(--border-soft);
  background: var(--bg-surface-muted);
}

.global-search-hints {
  display: flex;
  gap: var(--space-4);
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.global-search-hints kbd {
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
.global-search-enter-active {
  animation: fade-in var(--duration-base) var(--ease-out) both;
}

.global-search-leave-active {
  animation: fade-in var(--duration-fast) var(--ease-in) reverse both;
}

.global-search-enter-active .global-search {
  animation: scale-in var(--duration-slow) var(--ease-spring) both;
}

.global-search-leave-active .global-search {
  animation: scale-in var(--duration-fast) var(--ease-in) reverse both;
}

/* 响应式 */
@media (max-width: 767px) {
  .global-search-overlay {
    padding-top: 10vh;
  }

  .global-search {
    max-height: 70vh;
  }
}
</style>
