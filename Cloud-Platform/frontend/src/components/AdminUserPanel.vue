<script setup>
import EmptyState from "./EmptyState.vue";
import StatusPill from "./StatusPill.vue";

defineProps({
  users: { type: Array, default: () => [] },
  roles: { type: Array, default: () => [] }
});

const form = defineModel("form", { type: Object, required: true });
const emit = defineEmits(["create-user", "toggle-user", "reset-password"]);
</script>

<template>
  <section class="glass-card" data-reveal-scroll>
    <div class="section-head">
      <div>
        <div class="eyebrow">User Management</div>
        <h3>用户管理</h3>
        <p class="page-subtitle">创建账户并调整启停状态。</p>
      </div>
    </div>
    <div class="form-grid">
      <label class="field">
        <span>用户名</span>
        <input v-model="form.username" class="input" placeholder="例如：auditor" />
      </label>
      <label class="field">
        <span>初始密码</span>
        <input v-model="form.password" class="input" type="password" placeholder="至少 6 位" />
      </label>
      <label class="field">
        <span>角色</span>
        <select v-model="form.role" class="select">
          <option v-for="role in roles" :key="role.id" :value="role.name">{{ role.name }}</option>
        </select>
      </label>
    </div>
    <button class="btn" @click="emit('create-user')">创建用户</button>

    <table v-if="users.length" class="table">
      <thead>
        <tr><th>用户名</th><th>角色</th><th>状态</th><th>创建时间</th><th>操作</th></tr>
      </thead>
      <tbody>
        <tr v-for="user in users" :key="user.id">
          <td>{{ user.username }}</td>
          <td>{{ user.role }}</td>
          <td><StatusPill :label="user.is_active ? '启用' : '停用'" :tone="user.is_active ? 'success' : 'danger'" /></td>
          <td>{{ user.created_at }}</td>
          <td class="toolbar">
            <button class="btn secondary" @click="emit('toggle-user', user)">{{ user.is_active ? "停用" : "启用" }}</button>
            <button class="btn ghost" @click="emit('reset-password', user)">重置密码</button>
          </td>
        </tr>
      </tbody>
    </table>
    <EmptyState v-else title="暂无用户" compact />
  </section>
</template>
