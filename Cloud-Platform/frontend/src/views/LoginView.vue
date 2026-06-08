<script setup>
import { onMounted, reactive, ref, computed } from "vue";
import { useRouter } from "vue-router";

import http from "../api/client";
import { useMotionReveal } from "../composables/useMotionReveal";
import { useAuthStore } from "../stores/auth";
import { useToast } from "../composables/useToast";

const router = useRouter();
const authStore = useAuthStore();
const { success: showSuccess, error: showError } = useToast();

const loginForm = reactive({ username: "", password: "" });
const bootstrapForm = reactive({ username: "", password: "", bootstrapToken: "" });
const bootstrapState = ref(null);
const checking = ref(true);
const submitting = ref(false);
const error = ref("");
const pageRef = ref(null);

// 表单验证状态
const validation = reactive({
  username: { touched: false, valid: true, message: "" },
  password: { touched: false, valid: true, message: "" },
  bootstrapToken: { touched: false, valid: true, message: "" }
});

useMotionReveal(pageRef);

const isBootstrap = computed(() => bootstrapState.value?.needs_initial_admin);
const currentForm = computed(() => isBootstrap.value ? bootstrapForm : loginForm);

function validateField(field, value) {
  validation[field].touched = true;

  if (!value || value.trim() === "") {
    validation[field].valid = false;
    validation[field].message = "此字段不能为空";
    return false;
  }

  if (field === "password" && value.length < 6) {
    validation[field].valid = false;
    validation[field].message = "密码至少需要6个字符";
    return false;
  }

  validation[field].valid = true;
  validation[field].message = "";
  return true;
}

function validateForm() {
  const form = currentForm.value;
  const fields = isBootstrap.value
    ? ["username", "password", "bootstrapToken"]
    : ["username", "password"];

  let isValid = true;
  for (const field of fields) {
    if (!validateField(field, form[field])) {
      isValid = false;
    }
  }
  return isValid;
}

async function loadBootstrapState() {
  checking.value = true;
  error.value = "";
  try {
    bootstrapState.value = await http.get("/system/bootstrap-check");
  } catch (err) {
    error.value = err.message;
  } finally {
    checking.value = false;
  }
}

async function submit() {
  if (!validateForm()) {
    return;
  }

  submitting.value = true;
  error.value = "";
  try {
    if (isBootstrap.value) {
      await authStore.bootstrapAdmin(
        bootstrapForm.username,
        bootstrapForm.password,
        bootstrapForm.bootstrapToken
      );
      showSuccess("初始化成功", "管理员账户已创建，正在进入控制台...");
    } else {
      await authStore.login(loginForm.username, loginForm.password);
      showSuccess("登录成功", "欢迎回来！");
    }
    router.push("/dashboard");
  } catch (err) {
    error.value = err.message;
    showError("登录失败", err.message);
  } finally {
    submitting.value = false;
  }
}

onMounted(loadBootstrapState);
</script>

<template>
  <div ref="pageRef" class="login-wrap">
    <div class="login-shell">
      <!-- 品牌面板 -->
      <section class="login-brand" data-reveal>
        <div>
          <div class="eyebrow light">Greenhouse Robotics Platform</div>
          <h1 class="page-title light">温室机器人云端控制台</h1>
          <p class="page-subtitle light">任务、采集、设备与系统管理统一入口。</p>
        </div>

        <div class="login-highlight-grid">
          <div class="login-float-card">
            <span class="login-float-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
            </span>
            <span>任务</span>
            <strong>创建、调度、追踪</strong>
          </div>
          <div class="login-float-card">
            <span class="login-float-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </span>
            <span>采集</span>
            <strong>图库、上传、结果</strong>
          </div>
          <div class="login-float-card">
            <span class="login-float-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
              </svg>
            </span>
            <span>设备</span>
            <strong>状态、命令、运维</strong>
          </div>
        </div>

        <div class="login-stats">
          <div class="login-stat">
            <div class="login-stat-label">链路</div>
            <strong>MQTT + WebSocket</strong>
          </div>
          <div class="login-stat">
            <div class="login-stat-label">模式</div>
            <strong>Docker Compose 首发</strong>
          </div>
          <div class="login-stat">
            <div class="login-stat-label">定位</div>
            <strong>生产部署与日常值守</strong>
          </div>
        </div>
      </section>

      <!-- 表单面板 -->
      <section class="login-form-panel" data-reveal>
        <form class="stack login-form-stack" @submit.prevent="submit">
          <div class="panel-note">
            <div>
              <div class="eyebrow">{{ isBootstrap ? "Bootstrap" : "Sign In" }}</div>
              <h2 class="section-title login-form-title">
                {{ isBootstrap ? "初始化首个管理员" : "进入控制台" }}
              </h2>
            </div>
            <span class="status-pill" :class="isBootstrap ? 'warn' : ''">
              {{ isBootstrap ? "待初始化" : "生产入口" }}
            </span>
          </div>

          <!-- 加载状态 -->
          <div v-if="checking" class="login-loading">
            <div class="login-loading-spinner"></div>
            <p class="muted-text">正在检查系统初始化状态...</p>
          </div>

          <template v-else>
            <p v-if="isBootstrap" class="page-subtitle">
              当前系统尚未创建管理员账户。请输入部署时配置的初始化令牌与管理员密码，提交后会完成初始化并自动登录。
            </p>
            <p v-else class="page-subtitle">请输入现有管理员或操作员账户登录。</p>

            <!-- Bootstrap 表单 -->
            <template v-if="isBootstrap">
              <label class="field">
                <span>管理员用户名</span>
                <input
                  v-model="bootstrapForm.username"
                  class="input"
                  :class="{ error: validation.username.touched && !validation.username.valid }"
                  autocomplete="username"
                  @blur="validateField('username', bootstrapForm.username)"
                />
                <span
                  v-if="validation.username.touched && !validation.username.valid"
                  class="field-error"
                >
                  {{ validation.username.message }}
                </span>
              </label>

              <label class="field">
                <span>管理员密码</span>
                <input
                  v-model="bootstrapForm.password"
                  type="password"
                  class="input"
                  :class="{ error: validation.password.touched && !validation.password.valid }"
                  autocomplete="new-password"
                  @blur="validateField('password', bootstrapForm.password)"
                />
                <span
                  v-if="validation.password.touched && !validation.password.valid"
                  class="field-error"
                >
                  {{ validation.password.message }}
                </span>
              </label>

              <label class="field">
                <span>初始化令牌</span>
                <input
                  v-model="bootstrapForm.bootstrapToken"
                  type="password"
                  class="input"
                  :class="{ error: validation.bootstrapToken.touched && !validation.bootstrapToken.valid }"
                  autocomplete="one-time-code"
                  @blur="validateField('bootstrapToken', bootstrapForm.bootstrapToken)"
                />
                <span
                  v-if="validation.bootstrapToken.touched && !validation.bootstrapToken.valid"
                  class="field-error"
                >
                  {{ validation.bootstrapToken.message }}
                </span>
              </label>
            </template>

            <!-- 登录表单 -->
            <template v-else>
              <label class="field">
                <span>用户名</span>
                <input
                  v-model="loginForm.username"
                  class="input"
                  :class="{ error: validation.username.touched && !validation.username.valid }"
                  autocomplete="username"
                  @blur="validateField('username', loginForm.username)"
                />
                <span
                  v-if="validation.username.touched && !validation.username.valid"
                  class="field-error"
                >
                  {{ validation.username.message }}
                </span>
              </label>

              <label class="field">
                <span>密码</span>
                <input
                  v-model="loginForm.password"
                  type="password"
                  class="input"
                  :class="{ error: validation.password.touched && !validation.password.valid }"
                  autocomplete="current-password"
                  @blur="validateField('password', loginForm.password)"
                />
                <span
                  v-if="validation.password.touched && !validation.password.valid"
                  class="field-error"
                >
                  {{ validation.password.message }}
                </span>
              </label>
            </template>

            <!-- 错误提示 -->
            <div v-if="error" class="login-error" role="alert">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
              <span>{{ error }}</span>
            </div>

            <!-- 提交按钮 -->
            <button
              class="btn btn-lg"
              type="submit"
              :disabled="checking || submitting"
              :class="{ loading: submitting }"
            >
              <template v-if="!submitting">
                {{ isBootstrap ? "完成初始化并登录" : "进入控制台" }}
              </template>
            </button>

            <!-- 提示信息 -->
            <div class="status-box">
              <strong>{{ isBootstrap ? "初始化说明" : "建议流程" }}</strong>
              <div class="muted-text">
                {{
                  isBootstrap
                    ? "初始化完成后，可在系统管理页继续创建用户并注册机器人。初始化令牌来自部署环境中的 BOOTSTRAP_TOKEN。"
                    : "默认演示栈冷启动时会自动建立演示管理员；保留卷暖启动会沿用上次设置的密码。如需恢复 demo.env 中的演示账号，可执行 ./scripts/docker_stack.sh demo-reset-admin。"
                }}
              </div>
            </div>
          </template>
        </form>
      </section>
    </div>
  </div>
</template>

<style scoped>
.login-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-8) 0;
}

.login-loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--border-soft);
  border-top-color: var(--brand);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.login-error {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  background: var(--danger-50);
  border: 1px solid var(--danger-200);
  border-radius: var(--radius-sm);
  color: var(--danger-700);
  font-size: var(--text-sm);
}

.login-float-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: var(--radius-sm);
  color: var(--brand);
}

.login-float-card {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.login-float-card span {
  font-size: var(--text-xs);
  color: var(--text-inverse-secondary);
  text-transform: uppercase;
  letter-spacing: var(--tracking-wide);
}

.login-float-card strong {
  font-size: var(--text-sm);
  color: var(--text-inverse);
}
</style>
