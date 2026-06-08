<script setup>
import { onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";

import EmptyState from "../components/EmptyState.vue";
import SectionHero from "../components/SectionHero.vue";
import SkeletonBlock from "../components/SkeletonBlock.vue";
import StatusPill from "../components/StatusPill.vue";
import { useMotionReveal } from "../composables/useMotionReveal";
import { useToast } from "../composables/useToast";
import http from "../api/client";

const router = useRouter();
const robots = ref([]);
const loading = ref(false);
const error = ref("");
const submitting = ref(false);
const pageRef = ref(null);
const { success: showSuccess, error: showError } = useToast();

useMotionReveal(pageRef);

const form = reactive({
  name: "番茄温室高频采集",
  task_type: "phenotyping_capture",
  robot_id: "",
  priority: 3,
  route: "lane-1",
  capture_mode: "burst",
  capture_count: 3,
  capture_interval_seconds: 2,
  notes: ""
});

// 表单验证状态
const validation = reactive({
  name: { touched: false, valid: true, message: "" },
  robot_id: { touched: false, valid: true, message: "" }
});

const modalityOptions = [
  { value: "rgb", label: "RGB 图像" },
  { value: "depth", label: "深度图" },
  { value: "point_cloud", label: "点云" }
];
const selectedModalities = ref(["rgb", "depth", "point_cloud"]);

function validateField(field, value) {
  validation[field].touched = true;

  if (field === "name" && (!value || value.trim() === "")) {
    validation[field].valid = false;
    validation[field].message = "任务名称不能为空";
    return false;
  }

  if (field === "robot_id" && !value) {
    validation[field].valid = false;
    validation[field].message = "请选择目标机器人";
    return false;
  }

  validation[field].valid = true;
  validation[field].message = "";
  return true;
}

function validateForm() {
  let isValid = true;
  if (!validateField("name", form.name)) isValid = false;
  if (!validateField("robot_id", form.robot_id)) isValid = false;
  if (!selectedModalities.value.length) {
    error.value = "至少选择一种采集模态";
    isValid = false;
  }
  return isValid;
}

async function loadRobots() {
  loading.value = true;
  error.value = "";
  try {
    const payload = await http.get("/robots", { params: { page: 1, page_size: 100 } });
    robots.value = payload.items;
    if (robots.value.length && !form.robot_id) {
      form.robot_id = robots.value[0].id;
    }
  } catch (err) {
    error.value = err.message;
    showError("加载失败", err.message);
  } finally {
    loading.value = false;
  }
}

async function submit() {
  if (!validateForm()) {
    return;
  }

  error.value = "";
  submitting.value = true;
  try {
    const parameters = {
      route: form.route || "lane-1",
      capture_mode: form.capture_mode,
      capture_count: Number(form.capture_count) || 1,
      capture_interval_seconds: Number(form.capture_interval_seconds) || 1,
      modalities: selectedModalities.value
    };
    if (form.notes.trim()) {
      parameters.notes = form.notes.trim();
    }
    const data = await http.post("/tasks", {
      name: form.name,
      task_type: form.task_type,
      robot_id: form.robot_id,
      priority: Math.min(10, Math.max(1, Number(form.priority) || 3)),
      parameters
    });
    showSuccess("创建成功", "任务已创建，正在跳转...");
    router.push(`/tasks/${data.id}`);
  } catch (err) {
    error.value = err.message;
    showError("创建失败", err.message);
  } finally {
    submitting.value = false;
  }
}

onMounted(loadRobots);
</script>

<template>
  <div ref="pageRef" class="page-grid">
    <SectionHero
      eyebrow="Task Editor"
      title="新建采集任务"
      subtitle="选择机器人并配置采集参数。"
      split
      data-reveal
    >
      <template #actions>
        <button
          class="btn secondary"
          @click="loadRobots"
          :disabled="loading"
          :class="{ loading }"
        >
          <template v-if="!loading">刷新机器人</template>
        </button>
      </template>
      <template #aside>
        <div class="hero-kpis">
          <div class="hero-kpi">
            <span>可用设备</span>
            <strong>{{ robots.length }}</strong>
          </div>
          <div class="hero-kpi">
            <span>已选模态</span>
            <strong>{{ selectedModalities.length }}</strong>
          </div>
        </div>
      </template>
    </SectionHero>

    <section class="split-panel">
      <div class="stack">
        <!-- 基础设置 -->
        <section class="glass-card" data-reveal-scroll>
          <div class="section-head">
            <div>
              <div class="eyebrow">Basic Settings</div>
              <h3>基础设置</h3>
              <p class="page-subtitle">任务名称、类型、设备与优先级。</p>
            </div>
          </div>

          <!-- 加载状态 -->
          <SkeletonBlock v-if="loading" :lines="4" />

          <!-- 空状态 -->
          <EmptyState
            v-else-if="!robots.length"
            title="暂无机器人"
            description="请先到系统管理注册机器人。"
            compact
          />

          <!-- 表单 -->
          <div v-else class="form-grid">
            <label class="field">
              <span>任务名称</span>
              <input
                v-model="form.name"
                class="input"
                :class="{ error: validation.name.touched && !validation.name.valid }"
                @blur="validateField('name', form.name)"
              />
              <span
                v-if="validation.name.touched && !validation.name.valid"
                class="field-error"
              >
                {{ validation.name.message }}
              </span>
            </label>
            <label class="field">
              <span>任务类型</span>
              <select v-model="form.task_type" class="select">
                <option value="phenotyping_capture">表型采集</option>
                <option value="manual_image_import">手动图像导入</option>
              </select>
            </label>
            <label class="field">
              <span>目标机器人</span>
              <select
                v-model="form.robot_id"
                class="select"
                :class="{ error: validation.robot_id.touched && !validation.robot_id.valid }"
                @blur="validateField('robot_id', form.robot_id)"
              >
                <option value="">请选择机器人</option>
                <option
                  v-for="robot in robots"
                  :key="robot.id"
                  :value="robot.id"
                >
                  {{ robot.name }} / {{ robot.robot_code }}
                </option>
              </select>
              <span
                v-if="validation.robot_id.touched && !validation.robot_id.valid"
                class="field-error"
              >
                {{ validation.robot_id.message }}
              </span>
            </label>
            <label class="field">
              <span>优先级</span>
              <input
                v-model="form.priority"
                type="number"
                min="1"
                max="10"
                class="input"
              />
            </label>
          </div>
        </section>

        <!-- 采集配置 -->
        <section class="glass-card" data-reveal-scroll>
          <div class="section-head">
            <div>
              <div class="eyebrow">Capture Config</div>
              <h3>采集参数</h3>
              <p class="page-subtitle">路线、模式、频次与模态。</p>
            </div>
          </div>
          <div class="form-grid">
            <label class="field">
              <span>作业路线</span>
              <input
                v-model="form.route"
                class="input"
                placeholder="例如：lane-1"
              />
            </label>
            <label class="field">
              <span>采集模式</span>
              <select v-model="form.capture_mode" class="select">
                <option value="burst">连续采集</option>
                <option value="single">单次采集</option>
                <option value="inspection">巡检采集</option>
              </select>
            </label>
            <label class="field">
              <span>拍照张数</span>
              <input
                v-model="form.capture_count"
                type="number"
                min="1"
                max="30"
                class="input"
              />
            </label>
            <label class="field">
              <span>拍照间隔(秒)</span>
              <input
                v-model="form.capture_interval_seconds"
                type="number"
                min="1"
                max="60"
                class="input"
              />
            </label>
          </div>
          <div class="field">
            <span>采集模态</span>
            <div class="option-grid">
              <label
                v-for="item in modalityOptions"
                :key="item.value"
                class="option-item"
              >
                <input
                  v-model="selectedModalities"
                  type="checkbox"
                  :value="item.value"
                />
                <span>{{ item.label }}</span>
              </label>
            </div>
          </div>
          <label class="field">
            <span>备注说明</span>
            <textarea
              v-model="form.notes"
              class="textarea"
              rows="4"
              placeholder="可选：补充任务背景、关注区域或操作备注"
            ></textarea>
          </label>
        </section>
      </div>

      <!-- 预览面板 -->
      <aside class="glass-card sticky-column" data-reveal-scroll>
        <div class="section-head">
          <div>
            <div class="eyebrow">Preview</div>
            <h3>创建前检查</h3>
            <p class="page-subtitle">提交前确认关键信息。</p>
          </div>
        </div>
        <div class="kv-list">
          <div class="kv-row">
            <span>任务名称</span>
            <strong>{{ form.name || "-" }}</strong>
          </div>
          <div class="kv-row">
            <span>目标机器人</span>
            <strong>{{ robots.find((item) => item.id === form.robot_id)?.name || "-" }}</strong>
          </div>
          <div class="kv-row">
            <span>路线</span>
            <strong>{{ form.route || "-" }}</strong>
          </div>
          <div class="kv-row">
            <span>采集模式</span>
            <strong>{{ form.capture_mode }}</strong>
          </div>
          <div class="kv-row">
            <span>模态数量</span>
            <strong>{{ selectedModalities.length }}</strong>
          </div>
        </div>
        <div class="toolbar">
          <StatusPill
            v-for="item in selectedModalities"
            :key="item"
            :label="item"
          />
        </div>
        <div class="status-box">
          <strong>后续操作</strong>
          <div class="muted-text">
            创建后会进入任务详情页，可继续下发任务或补充上传数据。
          </div>
        </div>
        <p v-if="error" class="error-text" role="alert">{{ error }}</p>
        <button
          class="btn btn-lg"
          @click="submit"
          :disabled="submitting || loading"
          :class="{ loading: submitting }"
        >
          <template v-if="!submitting">创建任务</template>
        </button>
      </aside>
    </section>
  </div>
</template>
