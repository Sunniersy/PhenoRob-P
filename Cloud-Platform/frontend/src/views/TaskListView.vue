<script setup>
import { computed, onMounted, reactive, ref, watch } from "vue";
import { RouterLink } from "vue-router";

import ConfirmDialog from "../components/ConfirmDialog.vue";
import EmptyState from "../components/EmptyState.vue";
import MetricCard from "../components/MetricCard.vue";
import SectionHero from "../components/SectionHero.vue";
import SkeletonBlock from "../components/SkeletonBlock.vue";
import StatusPill from "../components/StatusPill.vue";
import { useMotionReveal } from "../composables/useMotionReveal";
import { useTaskActions } from "../composables/useTaskActions";
import { useToast } from "../composables/useToast";
import { tasks as tasksApi } from "../api";
import { TaskStatus } from "../constants/taskStatus";

const tasks = ref([]);
const total = ref(0);
const loading = ref(false);
const error = ref("");
const { success: showSuccess, error: showError } = useToast();

const filters = reactive({
  q: "",
  status: "",
  page: 1,
  page_size: 8
});

const pageRef = ref(null);
const confirmCancelVisible = ref(false);
const confirmCancelTaskId = ref(null);
let searchDebounce = null;

const { actionLoading, dispatchTask: doDispatch, retryTask: doRetry, cancelTask: doCancel } = useTaskActions(() => load());

useMotionReveal(pageRef);

const pageStats = computed(() => ({
  total: total.value,
  pending: tasks.value.filter((task) => task.status === TaskStatus.PENDING_DISPATCH).length,
  running: tasks.value.filter((task) => [
    TaskStatus.DISPATCHED,
    TaskStatus.ROBOT_ACKED,
    TaskStatus.RUNNING,
    TaskStatus.DATA_UPLOADING,
    TaskStatus.ANALYZING,
    TaskStatus.CANCELLING
  ].includes(task.status)).length,
  failed: tasks.value.filter((task) => task.status === TaskStatus.FAILED).length,
  totalPages: Math.max(1, Math.ceil(total.value / filters.page_size))
}));

// 状态筛选选项
const statusFilters = [
  { label: "全部", value: "" },
  { label: "待下发", value: TaskStatus.PENDING_DISPATCH },
  { label: "已下发", value: TaskStatus.DISPATCHED },
  { label: "执行中", value: TaskStatus.RUNNING },
  { label: "已完成", value: TaskStatus.COMPLETED },
  { label: "失败", value: TaskStatus.FAILED }
];

async function load() {
  loading.value = true;
  error.value = "";
  try {
    const payload = await tasksApi.list({
      page: filters.page,
      page_size: filters.page_size,
      q: filters.q || undefined,
      status: filters.status || undefined
    });
    tasks.value = payload.items;
    total.value = payload.total;
  } catch (err) {
    error.value = err.message;
    showError("加载失败", err.message);
  } finally {
    loading.value = false;
  }
}

async function dispatchTask(id) {
  error.value = "";
  try {
    await doDispatch(id);
    showSuccess("下发成功", "任务已成功下发到机器人");
  } catch (err) {
    error.value = err.message;
    showError("下发失败", err.message);
  }
}

async function retryTask(id) {
  error.value = "";
  try {
    await doRetry(id);
    showSuccess("重试成功", "任务已重新加入队列");
  } catch (err) {
    error.value = err.message;
    showError("重试失败", err.message);
  }
}

async function cancelTask(id) {
  error.value = "";
  try {
    await doCancel(id);
    showSuccess("取消成功", "任务已取消");
  } catch (err) {
    error.value = err.message;
    showError("取消失败", err.message);
  }
}

function promptCancelTask(id) {
  confirmCancelTaskId.value = id;
  confirmCancelVisible.value = true;
}

function onConfirmCancel() {
  confirmCancelVisible.value = false;
  if (confirmCancelTaskId.value) {
    cancelTask(confirmCancelTaskId.value);
    confirmCancelTaskId.value = null;
  }
}

function onCancelConfirm() {
  confirmCancelVisible.value = false;
  confirmCancelTaskId.value = null;
}

function applyStatus(status = "") {
  filters.status = status;
  filters.page = 1;
  load();
}

// 获取状态对应的tone
function getStatusTone(status) {
  switch (status) {
    case TaskStatus.FAILED:
      return "danger";
    case TaskStatus.ANALYZING:
    case TaskStatus.CANCELLING:
      return "warn";
    case TaskStatus.COMPLETED:
      return "success";
    default:
      return "default";
  }
}

watch(
  () => filters.q,
  () => {
    filters.page = 1;
    clearTimeout(searchDebounce);
    searchDebounce = setTimeout(load, 400);
  }
);

onMounted(load);
</script>

<template>
  <div ref="pageRef" class="page-grid">
    <SectionHero
      eyebrow="Task Center"
      title="任务中心"
      subtitle="查看任务状态并继续调度。"
      split
      data-reveal
    >
      <template #actions>
        <RouterLink class="btn" to="/tasks/create">创建任务</RouterLink>
        <button
          class="btn secondary"
          @click="load"
          :disabled="loading"
          :class="{ loading }"
        >
          <template v-if="!loading">刷新</template>
        </button>
      </template>
      <template #aside>
        <div class="hero-kpis">
          <div class="hero-kpi">
            <span>全部任务</span>
            <strong>{{ total }}</strong>
          </div>
          <div class="hero-kpi">
            <span>当前页</span>
            <strong>{{ filters.page }}</strong>
          </div>
        </div>
      </template>
    </SectionHero>

    <!-- 指标卡片 -->
    <section class="metric-grid list-stagger" data-reveal>
      <MetricCard
        label="任务总数"
        :value="pageStats.total"
        detail="全部已创建任务"
        accent
      />
      <MetricCard
        label="待下发"
        :value="pageStats.pending"
        detail="当前页待派发任务"
      />
      <MetricCard
        label="执行中"
        :value="pageStats.running"
        detail="当前页执行中任务"
      />
      <MetricCard
        label="失败任务"
        :value="pageStats.failed"
        detail="当前页失败任务"
      />
    </section>

    <!-- 筛选面板 -->
    <section class="glass-card" data-reveal-scroll>
      <div class="section-head">
        <div>
          <div class="eyebrow">Filter</div>
          <h3>搜索与筛选</h3>
        </div>
        <StatusPill :label="`${tasks.length} / ${total}`" />
      </div>
      <div class="form-grid">
        <label class="field">
          <span>搜索任务名</span>
          <input
            v-model="filters.q"
            class="input"
            placeholder="输入关键词搜索..."
          />
        </label>
        <label class="field">
          <span>每页数量</span>
          <select
            v-model="filters.page_size"
            class="select"
            @change="filters.page = 1; load()"
          >
            <option :value="8">8 条</option>
            <option :value="12">12 条</option>
            <option :value="20">20 条</option>
          </select>
        </label>
      </div>
      <div class="toolbar">
        <button
          v-for="sf in statusFilters"
          :key="sf.value"
          class="chip"
          :class="{ active: filters.status === sf.value }"
          :aria-pressed="String(filters.status === sf.value)"
          @click="applyStatus(sf.value)"
        >
          {{ sf.label }}
        </button>
      </div>
      <p v-if="error" class="error-text" role="alert">{{ error }}</p>
    </section>

    <!-- 加载状态 -->
    <template v-if="loading">
      <div class="task-board">
        <SkeletonBlock v-for="i in 4" :key="i" :lines="3" />
      </div>
    </template>

    <!-- 空状态 -->
    <EmptyState
      v-else-if="!tasks.length"
      title="当前筛选下没有任务"
      description="可以创建任务，或切换筛选查看其它状态。"
    />

    <!-- 任务列表 -->
    <section v-else class="task-board list-stagger">
      <article
        v-for="task in tasks"
        :key="task.id"
        class="glass-card task-card"
        data-reveal-scroll
      >
        <div class="task-card-head">
          <div>
            <h3>{{ task.name }}</h3>
            <div class="muted-text">{{ task.task_type }} · {{ task.robot_code }}</div>
          </div>
          <StatusPill
            :label="task.status"
            :tone="getStatusTone(task.status)"
          />
        </div>

        <!-- 进度条 -->
        <div class="task-progress">
          <div
            class="task-progress-bar"
            :style="{ width: `${task.progress}%` }"
            :class="{
              'progress-success': task.status === TaskStatus.COMPLETED,
              'progress-danger': task.status === TaskStatus.FAILED,
              'progress-running': [TaskStatus.RUNNING, TaskStatus.DATA_UPLOADING, TaskStatus.ANALYZING].includes(task.status)
            }"
          ></div>
        </div>

        <div class="task-meta">
          <div class="status-box">
            <span class="muted-text">进度</span>
            <strong class="task-meta-value">{{ task.progress }}%</strong>
          </div>
          <div class="status-box">
            <span class="muted-text">更新时间</span>
            <strong class="task-meta-value">{{ task.updated_at }}</strong>
          </div>
        </div>

        <div class="task-actions">
          <RouterLink class="btn secondary" :to="`/tasks/${task.id}`">
            查看详情
          </RouterLink>
          <button
            class="btn"
            @click="dispatchTask(task.id)"
            :disabled="task.status !== TaskStatus.PENDING_DISPATCH || !!actionLoading"
          >
            下发
          </button>
          <button
            class="btn secondary"
            @click="retryTask(task.id)"
            :disabled="task.status !== TaskStatus.FAILED || !!actionLoading"
          >
            重试
          </button>
          <button
            class="btn ghost"
            @click="promptCancelTask(task.id)"
            :disabled="![TaskStatus.PENDING_DISPATCH, TaskStatus.DISPATCHED, TaskStatus.ROBOT_ACKED, TaskStatus.RUNNING, TaskStatus.DATA_UPLOADING].includes(task.status) || !!actionLoading"
          >
            取消
          </button>
        </div>
      </article>
    </section>

    <!-- 分页 -->
    <section class="glass-card" data-reveal-scroll>
      <div class="section-head">
        <div>
          <div class="eyebrow">Pagination</div>
          <h3>翻页</h3>
        </div>
        <StatusPill :label="`${filters.page} / ${pageStats.totalPages}`" />
      </div>
      <div class="toolbar">
        <button
          class="btn secondary"
          :disabled="filters.page <= 1"
          @click="filters.page -= 1; load()"
        >
          上一页
        </button>
        <button
          class="btn secondary"
          :disabled="filters.page >= pageStats.totalPages"
          @click="filters.page += 1; load()"
        >
          下一页
        </button>
      </div>
    </section>

    <!-- 取消确认对话框 -->
    <ConfirmDialog
      :visible="confirmCancelVisible"
      title="取消任务"
      message="确定要取消该任务吗？取消后任务将停止执行。"
      @confirm="onConfirmCancel"
      @cancel="onCancelConfirm"
    />
  </div>
</template>

<style scoped>
.progress-success {
  background: var(--success-500);
}

.progress-danger {
  background: var(--danger-500);
}

.progress-running {
  background: var(--brand);
  animation: progress-pulse 2s ease-in-out infinite;
}

@keyframes progress-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}
</style>
