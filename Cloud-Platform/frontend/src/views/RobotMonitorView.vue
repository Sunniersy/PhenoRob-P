<script setup>
import { computed, onMounted, ref, watch } from "vue";

import CommandPanel from "../components/CommandPanel.vue";
import EmptyState from "../components/EmptyState.vue";
import MetricCard from "../components/MetricCard.vue";
import SectionHero from "../components/SectionHero.vue";
import SkeletonBlock from "../components/SkeletonBlock.vue";
import StatusPill from "../components/StatusPill.vue";
import { useMotionReveal } from "../composables/useMotionReveal";
import { useToast } from "../composables/useToast";
import { robots as robotsApi, tasks as tasksApi } from "../api";
import { TaskStatus } from "../constants/taskStatus";
import { useNotificationStore } from "../stores/notifications";
import { toSummaryRows } from "../utils/presenter";
import { mergeRealtimeRobotState, pickDefaultRobotId, robotToneForStatus } from "./robotMonitor.model";

const notificationStore = useNotificationStore();
const { success: showSuccess, error: showError } = useToast();
const robots = ref([]);
const tasks = ref([]);
const commands = ref([]);
const loading = ref(false);
const error = ref("");
const commandLoading = ref(false);
const selectedRobotId = ref("");
const commandTaskId = ref("");
const captureCount = ref(3);
const pageRef = ref(null);
let loadCommandsSeq = 0;

useMotionReveal(pageRef);

const displayRobots = computed(() =>
  mergeRealtimeRobotState(robots.value, notificationStore.robotStates, notificationStore.robotHeartbeats)
);

const selectedRobot = computed(() => displayRobots.value.find((robot) => robot.id === selectedRobotId.value) || null);
const selectedCommands = computed(() => notificationStore.robotCommands[selectedRobotId.value] || commands.value);
const eligibleTasks = computed(() =>
  tasks.value.filter((task) => [TaskStatus.DISPATCHED, TaskStatus.ROBOT_ACKED, TaskStatus.RUNNING, TaskStatus.DATA_UPLOADING].includes(task.status))
);

const robotTone = computed(() => robotToneForStatus(selectedRobot.value?.status));

const commandRows = (item) =>
  toSummaryRows(
    {
      task_id: item.params?.task_id,
      count: item.params?.count,
      result: item.result,
      error: item.error_message
    },
    6
  );

// 统计数据
const robotStats = computed(() => ({
  total: displayRobots.value.length,
  online: displayRobots.value.filter((r) => r.status !== "OFFLINE").length,
  offline: displayRobots.value.filter((r) => r.status === "OFFLINE").length
}));

async function load() {
  loading.value = true;
  error.value = "";
  try {
    const [robotList, taskList] = await Promise.all([
      robotsApi.list({ page: 1, page_size: 50 }),
      tasksApi.list({ page: 1, page_size: 50 })
    ]);
    robots.value = robotList.items;
    tasks.value = taskList.items;
    selectedRobotId.value = pickDefaultRobotId(selectedRobotId.value, robotList.items);
  } catch (err) {
    error.value = err.message;
    showError("加载失败", err.message);
  } finally {
    loading.value = false;
  }
}

async function loadCommands() {
  if (!selectedRobotId.value) return;
  const seq = ++loadCommandsSeq;
  try {
    const payload = await robotsApi.listCommands(selectedRobotId.value, { page: 1, page_size: 20 });
    if (seq === loadCommandsSeq) {
      commands.value = payload.items;
    }
  } catch (err) {
    if (seq === loadCommandsSeq) {
      error.value = err.message;
    }
  }
}

async function sendCommand(command, params = {}) {
  if (!selectedRobotId.value || commandLoading.value) return;
  commandLoading.value = true;
  error.value = "";
  try {
    await robotsApi.sendCommand(selectedRobotId.value, command, params);
    await loadCommands();

    const commandLabels = {
      start_charge: "开始充电",
      stop_charge: "停止充电",
      return_home: "返航",
      resume_task: "继续任务",
      pause_task: "暂停任务",
      cancel_task: "取消任务",
      capture_image: "采集拍照"
    };
    showSuccess("命令已发送", `${commandLabels[command] || command} 命令已下发`);
  } catch (err) {
    error.value = err.message;
    showError("命令失败", err.message);
  } finally {
    commandLoading.value = false;
  }
}

// 键盘导航
function handleRobotKeydown(event, robotId) {
  const robots = displayRobots.value;
  const currentIndex = robots.findIndex((r) => r.id === robotId);

  switch (event.key) {
    case "ArrowDown":
      event.preventDefault();
      if (currentIndex < robots.length - 1) {
        selectedRobotId.value = robots[currentIndex + 1].id;
      }
      break;
    case "ArrowUp":
      event.preventDefault();
      if (currentIndex > 0) {
        selectedRobotId.value = robots[currentIndex - 1].id;
      }
      break;
    case "Enter":
    case " ":
      event.preventDefault();
      selectedRobotId.value = robotId;
      break;
  }
}

watch(selectedRobotId, loadCommands);
onMounted(load);
</script>

<template>
  <div ref="pageRef" class="page-grid">
    <SectionHero
      eyebrow="Device Control"
      title="机器人控制台"
      subtitle="查看设备状态并下发控制命令。"
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
            <span>设备总数</span>
            <strong>{{ robotStats.total }}</strong>
          </div>
          <div class="hero-kpi">
            <span>在线设备</span>
            <strong>{{ robotStats.online }}</strong>
          </div>
          <div class="hero-kpi">
            <span>当前设备</span>
            <strong>{{ selectedRobot?.name || "--" }}</strong>
          </div>
        </div>
      </template>
    </SectionHero>

    <p v-if="error" class="error-text" role="alert">{{ error }}</p>

    <!-- 指标卡片 -->
    <section class="metric-grid list-stagger" data-reveal>
      <MetricCard
        label="设备总数"
        :value="robotStats.total"
        detail="已注册机器人数量"
        accent
      />
      <MetricCard
        label="在线设备"
        :value="robotStats.online"
        detail="当前在线设备"
      />
      <MetricCard
        label="离线设备"
        :value="robotStats.offline"
        detail="当前离线设备"
      />
    </section>

    <section class="robot-layout">
      <!-- 设备列表 -->
      <div class="stack">
        <section class="glass-card" data-reveal-scroll>
          <div class="section-head">
            <div>
              <div class="eyebrow">Device List</div>
              <h3>设备列表</h3>
            </div>
            <StatusPill :label="`${displayRobots.length} 台`" />
          </div>

          <!-- 加载状态 -->
          <SkeletonBlock v-if="loading" :lines="3" />

          <!-- 设备列表 -->
          <div
            v-else-if="displayRobots.length"
            class="stack list-stagger"
            role="listbox"
            aria-label="设备列表"
          >
            <button
              v-for="robot in displayRobots"
              :key="robot.id"
              class="robot-list-item"
              role="option"
              :aria-selected="String(robot.id === selectedRobotId)"
              :class="{
                active: robot.id === selectedRobotId,
                offline: robot.status === 'OFFLINE'
              }"
              @click="selectedRobotId = robot.id"
              @keydown="handleRobotKeydown($event, robot.id)"
              :tabindex="robot.id === selectedRobotId ? 0 : -1"
            >
              <div>
                <strong>{{ robot.name }}</strong>
                <div class="muted-text">{{ robot.robot_code }}</div>
              </div>
              <div class="robot-list-side">
                <StatusPill :label="robot.status" :tone="robotToneForStatus(robot.status)" />
                <div class="muted-text">{{ robot.last_heartbeat_at || "无心跳" }}</div>
              </div>
            </button>
          </div>

          <!-- 空状态 -->
          <EmptyState
            v-else
            title="暂无机器人"
            description="请先去系统管理注册机器人。"
            compact
          />
        </section>
      </div>

      <!-- 控制面板 -->
      <div class="stack">
        <template v-if="selectedRobot">
          <!-- 设备状态 -->
          <section class="glass-card robot-cockpit" data-reveal-scroll>
            <div class="section-head">
              <div>
                <div class="eyebrow">Cockpit</div>
                <h3>{{ selectedRobot.name }}</h3>
                <p class="page-subtitle">{{ selectedRobot.robot_code }} · {{ selectedRobot.protocol }}</p>
              </div>
              <StatusPill :label="selectedRobot.status" :tone="robotTone" />
            </div>

            <section class="metric-grid">
              <MetricCard
                label="在线状态"
                :value="selectedRobot.status"
                detail="根据心跳和状态流实时更新"
                :accent="selectedRobot.status !== 'OFFLINE'"
              />
              <MetricCard
                label="最近心跳"
                :value="selectedRobot.last_heartbeat_at || '-'"
                detail="最近设备上报"
              />
              <MetricCard
                label="电量"
                :value="selectedRobot.battery || '--'"
                detail="设备回传后实时更新"
              />
            </section>
          </section>

          <!-- 控制面板 -->
          <section class="glass-card" data-reveal-scroll>
            <div class="section-head">
              <div>
                <div class="eyebrow">Control Panel</div>
                <h3>控制面板</h3>
                <p class="page-subtitle">离线设备会自动禁用操作，在线设备可直接执行控制命令。</p>
              </div>
            </div>

            <!-- 状态与电源 -->
            <div class="control-cluster">
              <div class="control-cluster-head">
                <strong>状态与电源</strong>
                <StatusPill
                  :label="selectedRobot.status === 'OFFLINE' ? '设备离线' : '可下发命令'"
                  :tone="selectedRobot.status === 'OFFLINE' ? 'danger' : 'success'"
                />
              </div>
              <div class="control-grid">
                <button
                  class="btn"
                  :disabled="selectedRobot.status === 'OFFLINE' || commandLoading"
                  @click="sendCommand('start_charge')"
                >
                  开始充电
                </button>
                <button
                  class="btn secondary"
                  :disabled="selectedRobot.status === 'OFFLINE' || commandLoading"
                  @click="sendCommand('stop_charge')"
                >
                  停止充电
                </button>
                <button
                  class="btn secondary"
                  :disabled="selectedRobot.status === 'OFFLINE' || commandLoading"
                  @click="sendCommand('return_home')"
                >
                  返航/回桩
                </button>
              </div>
            </div>

            <!-- 任务控制 -->
            <div class="control-cluster">
              <div class="control-cluster-head">
                <strong>任务控制</strong>
              </div>
              <div class="control-grid">
                <button
                  class="btn"
                  :disabled="selectedRobot.status === 'OFFLINE' || commandLoading"
                  @click="sendCommand('resume_task')"
                >
                  继续任务
                </button>
                <button
                  class="btn secondary"
                  :disabled="selectedRobot.status === 'OFFLINE' || commandLoading"
                  @click="sendCommand('pause_task')"
                >
                  暂停任务
                </button>
                <button
                  class="btn danger"
                  :disabled="selectedRobot.status === 'OFFLINE' || commandLoading"
                  @click="sendCommand('cancel_task')"
                >
                  取消任务
                </button>
              </div>
            </div>

            <!-- 采集指令 -->
            <div class="control-cluster">
              <div class="control-cluster-head">
                <strong>采集指令</strong>
              </div>
              <div class="capture-panel">
                <label class="field">
                  <span>绑定任务</span>
                  <select v-model="commandTaskId" class="select">
                    <option value="">不绑定任务</option>
                    <option
                      v-for="task in eligibleTasks"
                      :key="task.id"
                      :value="task.id"
                    >
                      {{ task.name }} / {{ task.status }}
                    </option>
                  </select>
                </label>
                <label class="field">
                  <span>拍照数量</span>
                  <input
                    v-model="captureCount"
                    type="number"
                    min="1"
                    max="9"
                    class="input"
                  />
                </label>
                <button
                  class="btn"
                  :disabled="selectedRobot.status === 'OFFLINE' || commandLoading"
                  :class="{ loading: commandLoading }"
                  @click="sendCommand('capture_image', { task_id: commandTaskId || undefined, count: Math.min(9, Math.max(1, Number(captureCount) || 1)) })"
                >
                  <template v-if="!commandLoading">触发采集拍照</template>
                </button>
              </div>
            </div>
          </section>

          <!-- 命令时间线 -->
          <section class="glass-card" data-reveal-scroll>
            <div class="section-head">
              <div>
                <div class="eyebrow">Command Timeline</div>
                <h3>最近命令</h3>
                <p class="page-subtitle">查看命令状态变化。</p>
              </div>
            </div>
            <CommandPanel :commands="selectedCommands" :rows-for="commandRows" />
          </section>
        </template>

        <!-- 未选择设备 -->
        <EmptyState
          v-else
          title="还没有选中机器人"
          description="从左侧列表选择一台设备后，这里会显示设备状态和命令面板。"
        />
      </div>
    </section>
  </div>
</template>
