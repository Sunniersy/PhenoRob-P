<script setup>
import { ref, onErrorCaptured } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();
const error = ref(null);
const errorInfo = ref("");
const retryCount = ref(0);
const maxRetries = 3;

onErrorCaptured((err, instance, info) => {
  error.value = err;
  errorInfo.value = info;
  console.error("[ErrorBoundary] captured error:", err);
  console.error("[ErrorBoundary] component info:", info);
  return false;
});

function handleRetry() {
  if (retryCount.value < maxRetries) {
    retryCount.value++;
    error.value = null;
    errorInfo.value = "";
  } else {
    // 超过重试次数，跳转到首页
    router.push("/");
  }
}

function handleGoHome() {
  error.value = null;
  errorInfo.value = "";
  retryCount.value = 0;
  router.push("/");
}
</script>

<template>
  <div v-if="error" class="error-boundary">
    <div class="error-boundary-card">
      <div class="error-boundary-icon">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="8" x2="12" y2="12" />
          <line x1="12" y1="16" x2="12.01" y2="16" />
        </svg>
      </div>
      <h2>页面出现异常</h2>
      <p class="error-boundary-message">{{ error.message || "未知错误" }}</p>
      <p class="error-boundary-info">错误阶段: {{ errorInfo }}</p>
      <p v-if="retryCount > 0" class="error-boundary-retry">
        已重试 {{ retryCount }} / {{ maxRetries }} 次
      </p>
      <div class="error-boundary-actions">
        <button
          class="btn"
          @click="handleRetry"
          :disabled="retryCount >= maxRetries"
        >
          {{ retryCount < maxRetries ? "重试" : "返回首页" }}
        </button>
        <button class="btn secondary" @click="handleGoHome">
          返回首页
        </button>
      </div>
    </div>
  </div>
  <slot v-else />
</template>

<style scoped>
.error-boundary {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  padding: var(--space-8);
}

.error-boundary-card {
  max-width: 480px;
  text-align: center;
  padding: var(--space-8) var(--space-6);
  border-radius: var(--radius-xl);
  background: var(--bg-surface-strong);
  border: 1px solid var(--border-soft);
  box-shadow: var(--shadow-lg);
}

.error-boundary-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 80px;
  height: 80px;
  margin: 0 auto var(--space-6);
  background: var(--danger-50);
  border-radius: 50%;
  color: var(--danger-500);
}

.error-boundary-card h2 {
  margin: 0 0 var(--space-3);
  font-size: var(--text-xl);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
}

.error-boundary-message {
  color: var(--danger-600);
  margin: 0 0 var(--space-2);
  font-size: var(--text-base);
}

.error-boundary-info {
  color: var(--text-tertiary);
  font-size: var(--text-sm);
  margin: 0 0 var(--space-2);
}

.error-boundary-retry {
  color: var(--warning-600);
  font-size: var(--text-sm);
  margin: 0 0 var(--space-6);
}

.error-boundary-actions {
  display: flex;
  gap: var(--space-3);
  justify-content: center;
}
</style>
