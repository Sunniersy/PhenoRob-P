<script setup>
import StatusPill from "./StatusPill.vue";
import EmptyState from "./EmptyState.vue";

defineProps({
  asset: { type: Object, default: null },
  previewUrl: { type: Function, required: true },
  infoRows: { type: Array, default: () => [] },
  metaRows: { type: Array, default: () => [] },
  openLabel: { type: String, default: "新窗口预览" }
});
</script>

<template>
  <div class="detail-panel">
    <div class="section-head">
      <div>
        <div class="eyebrow">Asset Detail</div>
        <h3>资产详情</h3>
        <p class="page-subtitle">预览图片与关联信息。</p>
      </div>
      <a v-if="asset" class="btn secondary" :href="previewUrl(asset.id)" target="_blank" rel="noreferrer">{{ openLabel }}</a>
    </div>

    <EmptyState
      v-if="!asset"
      title="选择图片后显示详情"
      description="从图库选择一张图片后查看任务、机器人与元数据。"
    />

    <template v-else>
      <div class="detail-preview-wrap">
        <img class="detail-preview" :src="previewUrl(asset.id)" :alt="asset.file_name" />
      </div>
      <div class="detail-meta-grid">
        <div class="status-box">
          <strong>文件名</strong>
          <div class="summary-value">{{ asset.file_name }}</div>
        </div>
        <div class="status-box">
          <strong>机器人</strong>
          <div class="summary-value">{{ asset.robot_name || asset.robot_code }}</div>
        </div>
        <div class="status-box">
          <strong>任务</strong>
          <div class="summary-value">{{ asset.task_name }}</div>
        </div>
        <div class="status-box">
          <strong>对象键</strong>
          <div class="summary-value mono">{{ asset.object_key }}</div>
        </div>
      </div>
      <div class="status-box">
        <div class="section-head compact">
          <strong>资产信息</strong>
          <StatusPill :label="asset.asset_type" />
        </div>
        <div class="kv-list">
          <div v-for="row in infoRows" :key="row.key" class="kv-row">
            <span>{{ row.key }}</span>
            <strong>{{ row.value }}</strong>
          </div>
        </div>
      </div>
      <div class="status-box">
        <strong>元数据</strong>
        <div v-if="metaRows.length" class="kv-list">
          <div v-for="row in metaRows" :key="row.key" class="kv-row">
            <span>{{ row.key }}</span>
            <strong>{{ row.value }}</strong>
          </div>
        </div>
        <div v-else class="muted-text">暂无结构化元数据。</div>
      </div>
    </template>
  </div>
</template>
