<script setup>
defineProps({
  tasks: { type: Array, default: () => [] },
  robots: { type: Array, default: () => [] }
});

const filters = defineModel("filters", { type: Object, required: true });
const emit = defineEmits(["refresh"]);
</script>

<template>
  <section class="glass-card" data-reveal-scroll>
    <div class="section-head">
      <div>
        <div class="eyebrow">Filter Rail</div>
        <h3>筛选条件</h3>
        <p class="page-subtitle">按任务、设备与资产类型过滤正式入库资产。</p>
      </div>
    </div>
    <div class="form-grid">
      <label class="field">
        <span>按任务</span>
        <select v-model="filters.task_id" class="select" @change="emit('refresh')">
          <option value="">全部任务</option>
          <option v-for="task in tasks" :key="task.id" :value="task.id">{{ task.name }}</option>
        </select>
      </label>
      <label class="field">
        <span>按机器人</span>
        <select v-model="filters.robot_id" class="select" @change="emit('refresh')">
          <option value="">全部机器人</option>
          <option v-for="robot in robots" :key="robot.id" :value="robot.id">{{ robot.name }}</option>
        </select>
      </label>
      <label class="field">
        <span>资产类型</span>
        <select v-model="filters.asset_type" class="select" @change="emit('refresh')">
          <option value="">全部类型</option>
          <option value="IMAGE">IMAGE</option>
          <option value="DEPTH">DEPTH</option>
          <option value="POINT_CLOUD">POINT_CLOUD</option>
        </select>
      </label>
    </div>
  </section>
</template>
