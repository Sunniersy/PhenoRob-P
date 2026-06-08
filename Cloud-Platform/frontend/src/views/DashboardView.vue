<script setup>
import { computed, onMounted, ref } from "vue";

import EmptyState from "../components/EmptyState.vue";
import MetricCard from "../components/MetricCard.vue";
import SectionHero from "../components/SectionHero.vue";
import SkeletonBlock from "../components/SkeletonBlock.vue";
import StatusPill from "../components/StatusPill.vue";
import { useMotionReveal } from "../composables/useMotionReveal";
import { usePolling } from "../composables/usePolling";
import { useDashboardStore } from "../stores/dashboard";
import { useToast } from "../composables/useToast";

const dashboard = useDashboardStore();
const { info: showInfo } = useToast();
const pageRef = ref(null);

useMotionReveal(pageRef);

const readinessList = computed(() => Object.entries(dashboard.bootstrap?.checks || {}));
const readinessSummary = computed(() => ({
  ok: readinessList.value.filter(([, item]) => item.ok).length,
  total: readinessList.value.length
}));

usePolling(() => dashboard.fetchOverview(), 30000);

function handleRefresh() {
  dashboard.fetchOverview();
  showInfo("刷新中", "正在获取最新数据...");
}

onMounted(() => {
  dashboard.fetchOverview();
});
</script>

<template>
  <div ref="pageRef" class="page-grid">
    <SectionHero
      eyebrow="Operations Dashboard"
      title="农业设备云端运营总览"
      subtitle="汇总设备、任务、资产与系统就绪状态。"
      split
      data-reveal
    >
      <template #actions>
        <button
          class="btn secondary"
          @click="handleRefresh"
          :disabled="dashboard.loading"
          :class="{ loading: dashboard.loading }"
        >
          <template v-if="!dashboard.loading">刷新总览</template>
        </button>
        <router-link class="btn" to="/tasks/create">创建新任务</router-link>
      </template>
      <template #aside>
        <div class="dashboard-hero-status">
          <StatusPill
            :label="dashboard.bootstrap?.ok ? '系统就绪' : '依赖异常'"
            :tone="dashboard.bootstrap?.ok ? 'success' : 'danger'"
          />
          <div class="hero-kpis">
            <div class="hero-kpi">
              <span>在线设备</span>
              <strong>{{ dashboard.overview ? `${dashboard.overview.robot_online} / ${dashboard.overview.robot_total}` : "--" }}</strong>
            </div>
            <div class="hero-kpi">
              <span>依赖检查</span>
              <strong>{{ readinessSummary.ok }} / {{ readinessSummary.total }}</strong>
            </div>
            <div class="hero-kpi">
              <span>执行任务</span>
              <strong>{{ dashboard.overview?.running_task_total ?? "--" }}</strong>
            </div>
            <div class="hero-kpi">
              <span>活跃告警</span>
              <strong>{{ dashboard.overview?.recent_alerts?.length ?? 0 }}</strong>
            </div>
          </div>
        </div>
      </template>
    </SectionHero>

    <p v-if="dashboard.error" class="error-text" role="alert">{{ dashboard.error }}</p>

    <!-- 骨架屏加载状态 -->
    <template v-if="dashboard.loading">
      <div class="metric-grid">
        <SkeletonBlock v-for="i in 4" :key="i" :lines="2" />
      </div>
      <div class="dashboard-grid">
        <SkeletonBlock v-for="i in 4" :key="i" :lines="4" />
      </div>
    </template>

    <template v-else-if="dashboard.overview">
      <!-- 指标卡片 -->
      <section class="metric-grid list-stagger" data-reveal>
        <MetricCard
          label="执行中任务"
          :value="dashboard.overview.running_task_total"
          detail="当前正在流转的任务"
          accent
        />
        <MetricCard
          label="任务总数"
          :value="dashboard.overview.task_total"
          detail="累计创建任务"
        />
        <MetricCard
          label="资产总数"
          :value="dashboard.overview.asset_total"
          detail="已入库采集资产"
        />
        <MetricCard
          label="结果总数"
          :value="dashboard.overview.result_total"
          detail="已完成分析结果"
        />
      </section>

      <!-- 详情面板 -->
      <section class="dashboard-grid list-stagger">
        <!-- 依赖检查 -->
        <div class="glass-card" data-reveal-scroll>
          <div class="section-head">
            <div>
              <div class="eyebrow">Infrastructure</div>
              <h3>依赖检查</h3>
              <p class="page-subtitle">关键链路状态。</p>
            </div>
            <StatusPill
              :label="dashboard.bootstrap?.ok ? 'Ready' : 'Degraded'"
              :tone="dashboard.bootstrap?.ok ? 'success' : 'danger'"
            />
          </div>
          <div class="summary-grid">
            <div v-for="[key, item] in readinessList" :key="key" class="status-box">
              <strong>{{ key }}</strong>
              <div :class="item.ok ? 'ok-text' : 'error-text'">
                {{ item.ok ? "可用" : "异常" }}
              </div>
              <div class="muted-text">
                {{ item.details?.backend || item.details?.host || item.error || "检查通过" }}
              </div>
            </div>
          </div>
          <div v-if="dashboard.runtime" class="status-box">
            <strong>运行时</strong>
            <div class="kv-list">
              <div class="kv-row">
                <span>版本</span>
                <strong>{{ dashboard.runtime.version }}</strong>
              </div>
              <div class="kv-row">
                <span>队列</span>
                <strong>{{ dashboard.runtime.backends.task_queue.backend }}</strong>
              </div>
              <div class="kv-row">
                <span>存储</span>
                <strong>{{ dashboard.runtime.backends.storage.backend }}</strong>
              </div>
              <div class="kv-row">
                <span>最近离线扫描</span>
                <strong>{{ dashboard.runtime.last_offline_sweep_at || '-' }}</strong>
              </div>
            </div>
          </div>
        </div>

        <!-- 最近任务 -->
        <div class="glass-card" data-reveal-scroll>
          <div class="section-head">
            <div>
              <div class="eyebrow">Task Flow</div>
              <h3>最近任务</h3>
              <p class="page-subtitle">快速进入任务详情。</p>
            </div>
            <router-link class="btn secondary" to="/tasks">查看全部</router-link>
          </div>
          <div v-if="(dashboard.overview.recent_tasks || []).length" class="stack list-stagger">
            <router-link
              v-for="item in dashboard.overview.recent_tasks"
              :key="item.id"
              :to="`/tasks/${item.id}`"
              class="summary-item"
            >
              <div class="summary-item-main">
                <strong>{{ item.name }}</strong>
                <div class="summary-item-meta">
                  <span class="muted-text mono">{{ item.id }}</span>
                </div>
              </div>
              <StatusPill :label="item.status" />
            </router-link>
          </div>
          <EmptyState v-else title="暂无任务" description="先创建一个采集任务。" compact />
        </div>

        <!-- 最近资产 -->
        <div class="glass-card" data-reveal-scroll>
          <div class="section-head">
            <div>
              <div class="eyebrow">Asset Stream</div>
              <h3>最近采集资产</h3>
              <p class="page-subtitle">最新入库的采集内容。</p>
            </div>
            <router-link class="btn secondary" to="/data">打开图库</router-link>
          </div>
          <div v-if="(dashboard.overview.recent_assets || []).length" class="stack list-stagger">
            <div
              v-for="item in dashboard.overview.recent_assets"
              :key="item.id"
              class="summary-item"
            >
              <div class="summary-item-main">
                <strong>{{ item.file_name }}</strong>
                <div class="summary-item-meta">
                  <span class="muted-text">任务 {{ item.task_id }}</span>
                </div>
              </div>
              <StatusPill :label="item.asset_type" />
            </div>
          </div>
          <EmptyState v-else title="暂无采集资产" compact />
        </div>

        <!-- 告警与结果 -->
        <div class="glass-card" data-reveal-scroll>
          <div class="section-head">
            <div>
              <div class="eyebrow">Alerts & Results</div>
              <h3>告警与结果</h3>
              <p class="page-subtitle">最新异常与分析摘要。</p>
            </div>
          </div>
          <div class="stack">
            <div>
              <div class="section-head compact">
                <strong>最新告警</strong>
              </div>
              <div v-if="(dashboard.overview.recent_alerts || []).length" class="stack list-stagger">
                <div
                  v-for="item in dashboard.overview.recent_alerts"
                  :key="item.id"
                  class="summary-item"
                >
                  <div class="summary-item-main">
                    <strong>{{ item.source }}</strong>
                    <div class="muted-text">{{ item.message }}</div>
                  </div>
                  <span class="muted-text">{{ item.created_at }}</span>
                </div>
              </div>
              <EmptyState v-else title="暂无告警" compact />
            </div>
            <div>
              <div class="section-head compact">
                <strong>最新结果</strong>
              </div>
              <div v-if="(dashboard.overview.recent_results || []).length" class="stack list-stagger">
                <div
                  v-for="item in dashboard.overview.recent_results"
                  :key="item.task_id"
                  class="summary-item"
                >
                  <div class="summary-item-main">
                    <strong>{{ item.summary }}</strong>
                    <div class="muted-text">任务 {{ item.task_id }}</div>
                  </div>
                </div>
              </div>
              <EmptyState v-else title="暂无分析结果" compact />
            </div>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>
