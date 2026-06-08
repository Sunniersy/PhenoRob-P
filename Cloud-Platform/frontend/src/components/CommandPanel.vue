<script setup>
import EmptyState from "./EmptyState.vue";
import StatusPill from "./StatusPill.vue";

defineProps({
  commands: { type: Array, default: () => [] },
  rowsFor: { type: Function, required: true }
});
</script>

<template>
  <EmptyState v-if="!commands.length" title="暂无命令记录" description="选择设备并下发命令后会显示在这里。" compact />
  <div v-else class="command-list">
    <article v-for="item in commands" :key="item.id" class="command-item">
      <div class="control-cluster-head">
        <div>
          <strong>{{ item.command }}</strong>
          <div class="muted-text">操作人 {{ item.operator || "-" }} · {{ item.accepted_at }}</div>
        </div>
        <StatusPill
          :label="item.status"
          :tone="item.status === 'FAILED' ? 'danger' : item.status === 'ACKED' ? 'warn' : item.status === 'COMPLETED' ? 'success' : 'default'"
        />
      </div>
      <div class="kv-list">
        <div v-for="row in rowsFor(item)" :key="row.key" class="kv-row">
          <span>{{ row.key }}</span>
          <strong>{{ row.value }}</strong>
        </div>
        <div v-if="!rowsFor(item).length" class="muted-text">等待设备返回更多结构化信息。</div>
      </div>
    </article>
  </div>
</template>
