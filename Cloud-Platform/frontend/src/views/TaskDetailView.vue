<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";

import BreadcrumbNav from "../components/BreadcrumbNav.vue";
import EmptyState from "../components/EmptyState.vue";
import LightboxViewer from "../components/LightboxViewer.vue";
import MetricCard from "../components/MetricCard.vue";
import SectionHero from "../components/SectionHero.vue";
import SkeletonBlock from "../components/SkeletonBlock.vue";
import StatusPill from "../components/StatusPill.vue";
import TimelinePanel from "../components/TimelinePanel.vue";
import { useBlobCache } from "../composables/useBlobCache";
import { useMotionReveal } from "../composables/useMotionReveal";
import { useTaskActions } from "../composables/useTaskActions";
import { useToast } from "../composables/useToast";
import { tasks as tasksApi } from "../api";
import { authFetchBlob } from "../api/client";
import { TaskStatus } from "../constants/taskStatus";
import { useNotificationStore } from "../stores/notifications";
import { formatBytes, shortenText, toSummaryRows } from "../utils/presenter";

const route = useRoute();
const notificationStore = useNotificationStore();
const { success: showSuccess, error: showError } = useToast();
const detail = ref(null);
const loading = ref(false);
const error = ref("");
const pageRef = ref(null);

// Lightbox状态
const lightboxVisible = ref(false);
const lightboxIndex = ref(0);

const { actionLoading, dispatchTask: doDispatch, retryTask: doRetry, cancelTask: doCancel } = useTaskActions(() => load());

useMotionReveal(pageRef);

const { get: getCachedBlob, cache: blobCache } = useBlobCache();

const liveTaskUpdate = computed(() => notificationStore.taskUpdates[route.params.id] || null);
const liveAnalysis = computed(() => notificationStore.analysisByTask[route.params.id] || null);
const imageAssets = computed(() => (detail.value?.assets || []).filter((asset) => asset.asset_type === "IMAGE"));

// Lightbox图片列表
const lightboxImages = computed(() =>
  imageAssets.value.map((asset) => ({
    src: previewUrl(asset.id),
    alt: asset.file_name
  }))
);

const timelineWithSummary = computed(() =>
  (detail.value?.timeline || []).map((item) => ({
    ...item,
    rows: toSummaryRows(item.payload, 5)
  }))
);
const taskParameterRows = computed(() => toSummaryRows(detail.value?.parameters || {}, 8));
const resultRows = computed(() => toSummaryRows(detail.value?.result?.result_json || {}, 10));
const assetSummaryCards = computed(() =>
  (detail.value?.assets || []).map((asset) => ({
    id: asset.id,
    title: asset.file_name,
    type: asset.asset_type,
    size: formatBytes(asset.size_bytes),
    createdAt: asset.created_at,
    objectKey: shortenText(asset.object_key, 14, 8),
    hash: shortenText(asset.sha256, 10, 8)
  }))
);
const uploadSessionCards = computed(() =>
  (detail.value?.upload_sessions || []).map((item) => ({
    id: item.id,
    type: item.asset_type,
    status: item.status,
    objectKey: shortenText(item.object_key, 14, 8),
    hash: item.sha256 ? shortenText(item.sha256, 10, 8) : "-"
  }))
);

let reloadTimer = null;

function previewUrl(assetId) {
  const key = String(assetId);
  if (blobCache.value[key]) return blobCache.value[key];
  getCachedBlob(key, () => authFetchBlob(`/api/assets/${assetId}/download`)).catch(() => {});
  return "";
}

// 打开Lightbox
function openLightbox(assetId) {
  const index = imageAssets.value.findIndex((a) => a.id === assetId);
  if (index >= 0) {
    lightboxIndex.value = index;
    lightboxVisible.value = true;
  }
}

async function load() {
  loading.value = true;
  error.value = "";
  try {
    detail.value = await tasksApi.get(route.params.id);
  } catch (err) {
    error.value = err.message;
    showError("加载失败", err.message);
  } finally {
    loading.value = false;
  }
}

function scheduleReload() {
  if (reloadTimer) clearTimeout(reloadTimer);
  reloadTimer = setTimeout(() => {
    reloadTimer = null;
    load();
  }, 400);
}

async function dispatchTask() {
  error.value = "";
  try {
    await doDispatch(route.params.id);
    showSuccess("下发成功", "任务已成功下发到机器人");
  } catch (err) {
    error.value = err.message;
    showError("下发失败", err.message);
  }
}

async function retryTask() {
  error.value = "";
  try {
    await doRetry(route.params.id);
    showSuccess("重试成功", "任务已重新加入队列");
  } catch (err) {
    error.value = err.message;
    showError("重试失败", err.message);
  }
}

async function cancelTask() {
  error.value = "";
  try {
    await doCancel(route.params.id);
    showSuccess("取消成功", "任务已取消");
  } catch (err) {
    error.value = err.message;
    showError("取消失败", err.message);
  }
}

onMounted(load);

watch(liveTaskUpdate, (update) => {
  if (!update || !detail.value) return;
  detail.value = {
    ...detail.value,
    status: update.status || detail.value.status,
    progress: update.progress ?? detail.value.progress,
    current_message: update.message || detail.value.current_message
  };
  if ([TaskStatus.DATA_UPLOADING, "DATA_READY", TaskStatus.ANALYZING, TaskStatus.COMPLETED, TaskStatus.FAILED].includes(update.status)) {
    scheduleReload();
  }
});

watch(liveAnalysis, (update) => {
  if (!update || !detail.value) return;
  scheduleReload();
});

onBeforeUnmount(() => {
  if (reloadTimer) clearTimeout(reloadTimer);
});
</script>

<template>
  <div ref="pageRef" class="page-grid">
    <BreadcrumbNav
      :items="[
        { label: '任务中心', to: '/tasks' },
        { label: detail?.name || '任务详情' }
      ]"
    />
    <SectionHero
      eyebrow="Task Detail"
      :title="detail?.name || '任务详情'"
      subtitle="查看任务状态、资产、结果与时间线。"
      split
      data-reveal
    >
      <template #actions>
        <button
          class="btn secondary"
          @click="load"
          :disabled="loading"
          :class="{ loading }"
        >
          <template v-if="!loading">刷新</template>
        </button>
        <button
          class="btn"
          @click="dispatchTask"
          :disabled="detail?.status !== TaskStatus.PENDING_DISPATCH || !!actionLoading"
        >
          下发任务
        </button>
        <button
          class="btn secondary"
          @click="retryTask"
          :disabled="detail?.status !== TaskStatus.FAILED || !!actionLoading"
        >
          重试任务
        </button>
        <button
          class="btn ghost"
          @click="cancelTask"
          :disabled="![TaskStatus.PENDING_DISPATCH, TaskStatus.DISPATCHED, TaskStatus.ROBOT_ACKED, TaskStatus.RUNNING, TaskStatus.DATA_UPLOADING].includes(detail?.status) || !!actionLoading"
        >
          取消任务
        </button>
      </template>
      <template #aside>
        <div class="hero-kpis">
          <div class="hero-kpi">
            <span>任务状态</span>
            <strong>{{ liveTaskUpdate?.status || detail?.status || "--" }}</strong>
          </div>
          <div class="hero-kpi">
            <span>执行进度</span>
            <strong>{{ detail ? `${liveTaskUpdate?.progress ?? detail.progress}%` : "--" }}</strong>
          </div>
        </div>
      </template>
    </SectionHero>

    <p v-if="error" class="error-text" role="alert">{{ error }}</p>

    <!-- 加载状态 -->
    <template v-if="loading">
      <div class="metric-grid">
        <SkeletonBlock v-for="i in 4" :key="i" :lines="2" />
      </div>
      <div class="detail-grid">
        <SkeletonBlock v-for="i in 4" :key="i" :lines="4" />
      </div>
    </template>

    <template v-else-if="detail">
      <!-- 指标卡片 -->
      <section class="metric-grid list-stagger" data-reveal>
        <MetricCard
          label="任务状态"
          :value="liveTaskUpdate?.status || detail.status"
          detail="实时同步状态变化"
          accent
        />
        <MetricCard
          label="目标机器人"
          :value="detail.robot_code"
          detail="当前分配设备"
        />
        <MetricCard
          label="执行进度"
          :value="`${liveTaskUpdate?.progress ?? detail.progress}%`"
          detail="实时进度"
        />
        <MetricCard
          label="当前消息"
          :value="liveTaskUpdate?.message || detail.current_message || '-'"
          detail="最近反馈"
        />
      </section>

      <!-- 详情面板 -->
      <section class="detail-grid list-stagger">
        <div class="stack">
          <!-- 采集图片 -->
          <section class="glass-card" data-reveal-scroll>
            <div class="section-head">
              <div>
                <div class="eyebrow">Images</div>
                <h3>采集图片</h3>
              </div>
              <StatusPill :label="`${imageAssets.length} 张`" />
            </div>
            <div v-if="imageAssets.length" class="gallery-grid">
              <article
                v-for="asset in imageAssets"
                :key="asset.id"
                class="asset-card"
                @click="openLightbox(asset.id)"
              >
                <div class="asset-thumb-wrap">
                  <img
                    class="asset-thumb"
                    :src="previewUrl(asset.id)"
                    :alt="asset.file_name"
                  />
                </div>
                <div class="asset-card-body">
                  <strong>{{ asset.file_name }}</strong>
                  <div class="asset-card-meta">
                    <span>{{ asset.created_at }}</span>
                  </div>
                </div>
              </article>
            </div>
            <EmptyState
              v-else
              title="暂无采集图片"
              description="可去数据页导入真实文件，或让设备执行拍照命令。"
              compact
            />
          </section>

          <!-- 资产列表 -->
          <section class="glass-card" data-reveal-scroll>
            <div class="section-head">
              <div>
                <div class="eyebrow">Assets</div>
                <h3>资产列表</h3>
              </div>
            </div>
            <div v-if="assetSummaryCards.length" class="stack list-stagger">
              <div
                v-for="asset in assetSummaryCards"
                :key="asset.id"
                class="summary-item"
              >
                <div class="summary-item-main">
                  <strong>{{ asset.title }}</strong>
                  <div class="summary-item-meta">
                    <StatusPill :label="asset.type" />
                    <span class="muted-text">{{ asset.size }}</span>
                    <span class="muted-text">{{ asset.createdAt }}</span>
                  </div>
                </div>
                <div class="summary-item-side">
                  <span class="muted-text mono">对象 {{ asset.objectKey }}</span>
                  <span class="muted-text mono">哈希 {{ asset.hash }}</span>
                </div>
              </div>
            </div>
            <EmptyState v-else title="暂无已登记资产" compact />
          </section>

          <!-- 任务参数 -->
          <section class="glass-card" data-reveal-scroll>
            <div class="section-head">
              <div>
                <div class="eyebrow">Parameters</div>
                <h3>任务参数</h3>
              </div>
            </div>
            <div v-if="detail.failure_reason" class="status-box">
              <strong>失败原因</strong>
              <div>{{ detail.failure_reason }}</div>
            </div>
            <div v-if="taskParameterRows.length" class="kv-list">
              <div
                v-for="row in taskParameterRows"
                :key="row.key"
                class="kv-row"
              >
                <span>{{ row.key }}</span>
                <strong>{{ row.value }}</strong>
              </div>
            </div>
            <EmptyState v-else title="当前任务没有可展示的参数字段" compact />
          </section>

          <!-- 任务时间线 -->
          <section class="glass-card" data-reveal-scroll>
            <div class="section-head">
              <div>
                <div class="eyebrow">Timeline</div>
                <h3>任务时间线</h3>
              </div>
            </div>
            <TimelinePanel :items="timelineWithSummary" empty-title="暂无任务事件" />
          </section>
        </div>

        <div class="stack">
          <!-- 上传会话 -->
          <section class="glass-card" data-reveal-scroll>
            <div class="section-head">
              <div>
                <div class="eyebrow">Upload Sessions</div>
                <h3>上传会话</h3>
              </div>
            </div>
            <div v-if="uploadSessionCards.length" class="stack list-stagger">
              <div
                v-for="item in uploadSessionCards"
                :key="item.id"
                class="summary-item"
              >
                <div class="summary-item-main">
                  <strong>{{ item.type }}</strong>
                  <div class="summary-item-meta">
                    <StatusPill :label="item.status" />
                  </div>
                </div>
                <div class="summary-item-side">
                  <span class="muted-text mono">对象 {{ item.objectKey }}</span>
                  <span class="muted-text mono">哈希 {{ item.hash }}</span>
                </div>
              </div>
            </div>
            <EmptyState v-else title="暂无上传会话" compact />
          </section>

          <!-- 分析结果 -->
          <section class="glass-card" data-reveal-scroll>
            <div class="section-head">
              <div>
                <div class="eyebrow">Analysis</div>
                <h3>分析结果</h3>
              </div>
            </div>
            <div v-if="detail.result_ready" class="stack">
              <div class="status-box">
                <strong>摘要</strong>
                <div>{{ liveAnalysis?.summary || detail.result?.summary }}</div>
              </div>
              <div class="status-box">
                <strong>结果文件</strong>
                <div class="summary-value mono">
                  {{ shortenText(liveAnalysis?.result_object_key || detail.result?.result_object_key, 20, 12) }}
                </div>
              </div>
              <div class="status-box">
                <strong>结果字段</strong>
                <div v-if="resultRows.length" class="kv-list">
                  <div
                    v-for="row in resultRows"
                    :key="row.key"
                    class="kv-row"
                  >
                    <span>{{ row.key }}</span>
                    <strong>{{ row.value }}</strong>
                  </div>
                </div>
                <div v-else class="muted-text">暂无结构化结果字段。</div>
              </div>
            </div>
            <EmptyState
              v-else
              :title="detail.analysis_status === 'DISABLED' ? '当前任务未启用分析服务' : '分析结果尚未生成'"
              :description="detail.analysis_status === 'DISABLED' ? '任务已完成资产闭环，但当前部署未配置外部分析服务。' : ''"
              compact
            />
          </section>
        </div>
      </section>
    </template>

    <!-- Lightbox查看器 -->
    <LightboxViewer
      v-model:visible="lightboxVisible"
      :images="lightboxImages"
      :initial-index="lightboxIndex"
    />
  </div>
</template>

<style scoped>
.asset-card {
  cursor: pointer;
}
</style>
