<script setup>
import EmptyState from "./EmptyState.vue";
import StatusPill from "./StatusPill.vue";

defineProps({
  robots: { type: Array, default: () => [] }
});

const form = defineModel("form", { type: Object, required: true });
const emit = defineEmits(["create-robot"]);
</script>

<template>
  <section class="glass-card" data-reveal-scroll>
    <div class="section-head">
      <div>
        <div class="eyebrow">Device Registry</div>
        <h3>新增机器人</h3>
        <p class="page-subtitle">登记设备基础信息与能力。</p>
      </div>
    </div>
    <div class="form-grid">
      <label class="field">
        <span>机器人编码</span>
        <input v-model="form.robot_code" class="input" placeholder="robot-002" />
      </label>
      <label class="field">
        <span>机器人名称</span>
        <input v-model="form.name" class="input" placeholder="温室采集机器人 002" />
      </label>
      <label class="field">
        <span>协议</span>
        <select v-model="form.protocol" class="select">
          <option value="mqtt">mqtt</option>
        </select>
      </label>
      <label class="field">
        <span>传感器能力（逗号分隔）</span>
        <input v-model="form.sensors" class="input" placeholder="rgb, depth, point_cloud" />
      </label>
      <label class="field">
        <span>执行器能力（逗号分隔）</span>
        <input v-model="form.actuators" class="input" placeholder="capture_image, return_home, start_charge" />
      </label>
      <label class="field">
        <span>所在区域</span>
        <input v-model="form.zone" class="input" placeholder="greenhouse-a" />
      </label>
      <label class="field">
        <span>作业线路</span>
        <input v-model="form.line" class="input" placeholder="lane-1" />
      </label>
      <label class="field">
        <span>设备厂商</span>
        <input v-model="form.vendor" class="input" placeholder="phenobot-lab" />
      </label>
    </div>
    <button class="btn" @click="emit('create-robot')">注册机器人</button>

    <div class="section-head compact">
      <div>
        <div class="eyebrow">Fleet Overview</div>
        <h3>机器人概览</h3>
      </div>
    </div>
    <table v-if="robots.length" class="table">
      <thead>
        <tr><th>名称</th><th>编码</th><th>状态</th><th>最近心跳</th></tr>
      </thead>
      <tbody>
        <tr v-for="robot in robots" :key="robot.id">
          <td>{{ robot.name }}</td>
          <td>{{ robot.robot_code }}</td>
          <td><StatusPill :label="robot.status" :tone="robot.status === 'OFFLINE' ? 'danger' : 'success'" /></td>
          <td>{{ robot.last_heartbeat_at || "-" }}</td>
        </tr>
      </tbody>
    </table>
    <EmptyState v-else title="暂无机器人" compact />
  </section>
</template>
