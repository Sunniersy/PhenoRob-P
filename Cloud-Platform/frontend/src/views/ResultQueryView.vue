<script setup>
import { computed, onMounted, reactive, ref, watch } from "vue";

import EmptyState from "../components/EmptyState.vue";
import SectionHero from "../components/SectionHero.vue";
import SkeletonBlock from "../components/SkeletonBlock.vue";
import StatusPill from "../components/StatusPill.vue";
import { useMotionReveal } from "../composables/useMotionReveal";
import { useToast } from "../composables/useToast";
import { results as resultsApi } from "../api";
import { shortenText } from "../utils/presenter";

const results = ref([]);
const total = ref(0);
const loading = ref(false);
const error = ref("");
const downloading = ref(null);
const pageRef = ref(null);
const { success: showSuccess, error: showError } = useToast();

const filters = reactive({
  q: "",
  page: 1,
  page_size: 10
});

let searchDebounce = null;

useMotionReveal(pageRef);

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / filters.page_size)));

async function load() {
  loading.value = true;
  error.value = "";
  try {
    const payload = await resultsApi.list({
      page: filters.page,
      page_size: filters.page_size,
      q: filters.q || undefined
    });
    results.value = payload.items;
    total.value = payload.total;
  } catch (err) {
    error.value = err.message;
    showError("加载失败", err.message);
  } finally {
    loading.value = false;
  }
}

async function downloadResult(taskId) {
  downloading.value = taskId;
  error.value = "";
  try {
    const blob = await resultsApi.download(taskId);
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `result-${taskId}.json`;
    a.click();
    URL.revokeObjectURL(url);
    showSuccess("下载成功", `结果文件已下载`);
  } catch (err) {
    error.value = err.message;
    showError("下载失败", err.message);
  } finally {
    downloading.value = null;
  }
}

// 搜索防抖
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
      eyebrow="Results Center"
      title="结果中心"
      subtitle="查看分析摘要、关联任务和结果文件。"
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
      </template>
      <template #aside>
        <div class="hero-kpis">
          <div class="hero-kpi">
            <span>结果总数</span>
            <strong>{{ total }}</strong>
          </div>
          <div class="hero-kpi">
            <span>当前页</span>
            <strong>{{ filters.page }}</strong>
          </div>
        </div>
      </template>
    </SectionHero>

    <!-- 搜索和筛选 -->
    <section class="glass-card" data-reveal-scroll>
      <div class="section-head">
        <div>
          <div class="eyebrow">Search</div>
          <h3>搜索与翻页</h3>
        </div>
        <StatusPill :label="`${results.length} / ${total}`" />
      </div>
      <div class="form-grid">
        <label class="field">
          <span>搜索摘要</span>
          <input
            v-model="filters.q"
            class="input"
            placeholder="输入关键词搜索..."
          />
        </label>
        <label class="field">
          <span>每页数量</span>
          <select v-model="filters.page_size" class="select" @change="filters.page = 1; load()">
            <option :value="10">10 条</option>
            <option :value="20">20 条</option>
          </select>
        </label>
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
          :disabled="filters.page >= totalPages"
          @click="filters.page += 1; load()"
        >
          下一页
        </button>
      </div>
      <p v-if="error" class="error-text" role="alert">{{ error }}</p>
    </section>

    <!-- 结果列表 -->
    <section class="glass-card" data-reveal-scroll>
      <div class="section-head">
        <div>
          <div class="eyebrow">Analysis Results</div>
          <h3>结果列表</h3>
        </div>
        <StatusPill :label="`${filters.page} / ${totalPages}`" />
      </div>

      <!-- 加载状态 -->
      <SkeletonBlock v-if="loading" :lines="4" />

      <!-- 空状态 -->
      <EmptyState
        v-else-if="!results.length"
        title="暂无分析结果"
        description="如果当前部署未配置外部分析服务，任务完成后这里会保持为空。"
      />

      <!-- 结果表格 -->
      <div v-else class="table-wrapper">
        <table class="table list-stagger">
          <thead>
            <tr>
              <th>任务 ID</th>
              <th>摘要</th>
              <th>结果对象</th>
              <th>创建时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in results" :key="item.id">
              <td class="mono">{{ item.task_id }}</td>
              <td>{{ item.summary }}</td>
              <td class="mono">{{ shortenText(item.result_object_key, 24, 12) }}</td>
              <td>{{ item.created_at }}</td>
              <td class="toolbar">
                <router-link class="btn secondary btn-sm" :to="`/tasks/${item.task_id}`">
                  任务详情
                </router-link>
                <button
                  class="btn ghost btn-sm"
                  @click="downloadResult(item.task_id)"
                  :disabled="downloading === item.task_id"
                  :class="{ loading: downloading === item.task_id }"
                >
                  <template v-if="downloading !== item.task_id">下载结果</template>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>
