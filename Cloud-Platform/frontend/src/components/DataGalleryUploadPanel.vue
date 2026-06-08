<script setup>
import StatusPill from "./StatusPill.vue";

defineProps({
  robots: { type: Array, default: () => [] },
  uploadCount: { type: Number, default: 0 },
  uploading: { type: Boolean, default: false }
});

const form = defineModel("form", { type: Object, required: true });
const emit = defineEmits(["file-change", "submit"]);
</script>

<template>
  <section class="glass-card" data-reveal-scroll>
    <div class="section-head">
      <div>
        <div class="eyebrow">Manual Import</div>
        <h3>手动导入资产</h3>
      </div>
      <StatusPill label="正式功能" tone="success" />
    </div>
    <p class="page-subtitle">创建正式导入任务，上传真实文件并写入对象存储与资产表。</p>
    <div class="form-grid">
      <label class="field">
        <span>目标机器人</span>
        <select v-model="form.robot_id" class="select">
          <option value="">请选择机器人</option>
          <option v-for="robot in robots" :key="robot.id" :value="robot.id">{{ robot.name }}</option>
        </select>
      </label>
      <label class="field">
        <span>任务名模板</span>
        <input v-model="form.task_name" class="input" />
      </label>
    </div>
    <label class="field">
      <span>上传文件</span>
      <input class="input" type="file" accept="image/*,.svg,.json" multiple @change="emit('file-change', $event)" />
    </label>
    <button class="btn" @click="emit('submit')" :disabled="uploading">
      {{ uploading ? "上传中..." : `导入 ${uploadCount} 个文件` }}
    </button>
  </section>
</template>
