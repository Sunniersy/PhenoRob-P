<script setup>
import { computed, onMounted, reactive, ref } from "vue";

import AdminAlertPanel from "../components/AdminAlertPanel.vue";
import BaseModal from "../components/BaseModal.vue";
import AdminRobotPanel from "../components/AdminRobotPanel.vue";
import AdminSystemStatusPanel from "../components/AdminSystemStatusPanel.vue";
import AdminUserPanel from "../components/AdminUserPanel.vue";
import MetricCard from "../components/MetricCard.vue";
import SectionHero from "../components/SectionHero.vue";
import SkeletonBlock from "../components/SkeletonBlock.vue";
import { useMotionReveal } from "../composables/useMotionReveal";
import { useToast } from "../composables/useToast";
import { admin as adminApi, robots as robotsApi } from "../api";
import { parseCommaList } from "../utils/presenter";
import { useAdminStore } from "../stores/admin";

const admin = useAdminStore();
const pageRef = ref(null);
const actionLoading = ref("");
const resetPasswordTarget = ref(null);
const resetPasswordValue = ref("");
const { success: showSuccess, error: showError } = useToast();

useMotionReveal(pageRef);

const userForm = reactive({
  username: "",
  password: "",
  role: ""
});

const robotForm = reactive({
  robot_code: "",
  name: "",
  protocol: "mqtt",
  sensors: "rgb, depth, point_cloud",
  actuators: "capture_image, return_home, start_charge",
  zone: "greenhouse-a",
  line: "lane-1",
  vendor: "phenobot-lab"
});

const overviewStats = ref([
  { label: "可用检查", value: "0", detail: "依赖就绪状态" },
  { label: "用户总数", value: "0", detail: "当前账户规模" },
  { label: "机器人总数", value: "0", detail: "已登记设备" },
  { label: "活动告警", value: "0", detail: "待关注告警数" }
]);

async function load() {
  const result = await admin.fetchAll();
  if (result) {
    const { bootstrap, userList, roleList, robotList, alertList } = result;
    overviewStats.value = [
      {
        label: "可用检查",
        value: `${Object.values(bootstrap.checks || {}).filter((item) => item.ok).length}/${Object.keys(bootstrap.checks || {}).length}`,
        detail: bootstrap.initialization_ok ? "依赖与初始化已完成" : "依赖可用但尚未完成初始化"
      },
      { label: "用户总数", value: String(userList.total), detail: "可登录系统的账户数" },
      { label: "机器人总数", value: String(robotList.total), detail: "在控设备总量" },
      { label: "活动告警", value: String(alertList.total), detail: "需要人工回看的告警数" }
    ];
    if (!userForm.role && roleList.items.length) {
      userForm.role = roleList.items[0].name;
    }
  }
}

async function createUser() {
  if (!userForm.username.trim()) {
    admin.error = "用户名不能为空";
    return;
  }
  if (userForm.password.length < 6) {
    admin.error = "密码至少需要 6 个字符";
    return;
  }
  actionLoading.value = "createUser";
  admin.error = "";
  try {
    await adminApi.createUser({ ...userForm });
    userForm.username = "";
    userForm.password = "";
    await load();
    showSuccess("创建成功", `用户 ${userForm.username} 已创建`);
  } catch (err) {
    admin.error = err.message;
    showError("创建失败", err.message);
  } finally {
    actionLoading.value = "";
  }
}

async function createRobot() {
  if (!robotForm.robot_code.trim() || !robotForm.name.trim()) {
    admin.error = "机器人编码和名称不能为空";
    return;
  }
  actionLoading.value = "createRobot";
  admin.error = "";
  try {
    await robotsApi.register({
      robot_code: robotForm.robot_code.trim(),
      name: robotForm.name.trim(),
      protocol: robotForm.protocol,
      capabilities: {
        sensors: parseCommaList(robotForm.sensors),
        actuators: parseCommaList(robotForm.actuators)
      },
      metadata: {
        zone: robotForm.zone.trim(),
        line: robotForm.line.trim(),
        vendor: robotForm.vendor.trim()
      }
    });
    const robotName = robotForm.name;
    robotForm.robot_code = "";
    robotForm.name = "";
    await load();
    showSuccess("注册成功", `机器人 ${robotName} 已注册`);
  } catch (err) {
    admin.error = err.message;
    showError("注册失败", err.message);
  } finally {
    actionLoading.value = "";
  }
}

async function toggleUser(user) {
  actionLoading.value = `toggle-${user.id}`;
  admin.error = "";
  try {
    await adminApi.toggleUserStatus(user.id, !user.is_active);
    await load();
    showSuccess("操作成功", `用户 ${user.username} 已${user.is_active ? '禁用' : '启用'}`);
  } catch (err) {
    admin.error = err.message;
    showError("操作失败", err.message);
  } finally {
    actionLoading.value = "";
  }
}

function openResetPassword(user) {
  resetPasswordTarget.value = user;
  resetPasswordValue.value = "";
}

function closeResetPassword() {
  resetPasswordTarget.value = null;
  resetPasswordValue.value = "";
}

const resetModalVisible = computed(() => !!resetPasswordTarget.value);

async function submitResetPassword() {
  if (resetPasswordValue.value.length < 6) {
    admin.error = "密码至少需要 6 个字符";
    return;
  }
  actionLoading.value = "resetPassword";
  admin.error = "";
  try {
    await adminApi.resetPassword(resetPasswordTarget.value.id, resetPasswordValue.value);
    closeResetPassword();
    await load();
    showSuccess("重置成功", "密码已重置");
  } catch (err) {
    admin.error = err.message;
    showError("重置失败", err.message);
  } finally {
    actionLoading.value = "";
  }
}

async function acknowledgeAlert(alert) {
  actionLoading.value = `alert-${alert.id}`;
  admin.error = "";
  try {
    await adminApi.acknowledgeAlert(alert.id, !alert.is_acknowledged);
    await load();
    showSuccess("操作成功", `告警已${alert.is_acknowledged ? '取消确认' : '确认'}`);
  } catch (err) {
    admin.error = err.message;
    showError("操作失败", err.message);
  } finally {
    actionLoading.value = "";
  }
}

onMounted(load);
</script>

<template>
  <div ref="pageRef" class="page-grid">
    <SectionHero
      eyebrow="System Admin"
      title="系统管理"
      subtitle="管理用户、设备与系统状态。"
      split
      data-reveal
    >
      <template #actions>
        <button
          class="btn secondary"
          @click="load"
          :disabled="admin.loading"
          :class="{ loading: admin.loading }"
        >
          <template v-if="!admin.loading">刷新</template>
        </button>
      </template>
      <template #aside>
        <div class="hero-kpis">
          <div class="hero-kpi">
            <span>可用检查</span>
            <strong>{{ overviewStats[0]?.value || "0" }}</strong>
          </div>
          <div class="hero-kpi">
            <span>活动告警</span>
            <strong>{{ admin.alerts.length }}</strong>
          </div>
        </div>
      </template>
    </SectionHero>

    <p v-if="admin.error" class="error-text" role="alert">{{ admin.error }}</p>

    <!-- 加载状态 -->
    <template v-if="admin.loading">
      <div class="metric-grid">
        <SkeletonBlock v-for="i in 4" :key="i" :lines="2" />
      </div>
    </template>

    <!-- 指标卡片 -->
    <section v-else class="metric-grid list-stagger" data-reveal>
      <MetricCard
        v-for="(item, index) in overviewStats"
        :key="item.label"
        :label="item.label"
        :value="item.value"
        :detail="item.detail"
        :accent="index === 0"
      />
    </section>

    <!-- 管理面板 -->
    <section class="admin-grid list-stagger">
      <div class="stack">
        <AdminSystemStatusPanel :system="admin.system" :loading="admin.loading" />
        <AdminUserPanel
          :users="admin.users"
          :roles="admin.roles"
          v-model:form="userForm"
          @create-user="createUser"
          @toggle-user="toggleUser"
          @reset-password="openResetPassword"
        />
      </div>

      <div class="stack">
        <AdminRobotPanel :robots="admin.robots" v-model:form="robotForm" @create-robot="createRobot" />
        <AdminAlertPanel :alerts="admin.alerts" @toggle-alert="acknowledgeAlert" />
      </div>
    </section>

    <!-- 重置密码模态框 -->
    <BaseModal
      :visible="resetModalVisible"
      title="重置密码"
      @close="closeResetPassword"
    >
      <p class="page-subtitle">
        为 {{ resetPasswordTarget?.username }} 设置新密码（至少 6 个字符）。
      </p>
      <label class="field">
        <span>新密码</span>
        <input
          v-model="resetPasswordValue"
          type="password"
          class="input"
          autocomplete="new-password"
          placeholder="输入新密码"
          @keyup.enter="submitResetPassword"
        />
      </label>
      <template #footer>
        <button class="btn secondary" @click="closeResetPassword">取消</button>
        <button
          class="btn"
          @click="submitResetPassword"
          :disabled="actionLoading === 'resetPassword'"
          :class="{ loading: actionLoading === 'resetPassword' }"
        >
          <template v-if="actionLoading !== 'resetPassword'">确认重置</template>
        </button>
      </template>
    </BaseModal>
  </div>
</template>
