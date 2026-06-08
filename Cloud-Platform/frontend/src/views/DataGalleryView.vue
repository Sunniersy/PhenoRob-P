<script setup>
import { computed, onMounted, reactive, ref } from "vue";

import AssetDetailPanel from "../components/AssetDetailPanel.vue";
import DataGalleryFilterPanel from "../components/DataGalleryFilterPanel.vue";
import DataGalleryUploadPanel from "../components/DataGalleryUploadPanel.vue";
import EmptyState from "../components/EmptyState.vue";
import UploadProgress from "../components/UploadProgress.vue";
import GalleryGrid from "../components/GalleryGrid.vue";
import LightboxViewer from "../components/LightboxViewer.vue";
import SectionHero from "../components/SectionHero.vue";
import SkeletonBlock from "../components/SkeletonBlock.vue";
import StatusPill from "../components/StatusPill.vue";
import { useBlobCache } from "../composables/useBlobCache";
import { useMotionReveal } from "../composables/useMotionReveal";
import { useToast } from "../composables/useToast";
import { assets as assetsApi, tasks as tasksApi, robots as robotsApi } from "../api";
import { authFetchBlob } from "../api/client";
import { formatBytes, shortenText, toSummaryRows } from "../utils/presenter";
import { useDataGalleryStore } from "../stores/dataGallery";

const gallery = useDataGalleryStore();
const tasks = ref([]);
const robots = ref([]);
const selectedAsset = ref(null);
const railCollapsed = ref(false);
const pageRef = ref(null);
const uploadFiles = ref([]);
const uploading = ref(false);
const uploadCurrentIndex = ref(0);
const uploadCurrentProgress = ref(0);
const assetLoading = ref(false);
const { get: getCachedBlob, cache: blobCache } = useBlobCache();
const { success: showSuccess, error: showError } = useToast();

// Lightbox状态
const lightboxVisible = ref(false);
const lightboxIndex = ref(0);

useMotionReveal(pageRef);

const filters = gallery.filters;

const importForm = reactive({
  robot_id: "",
  task_name: "手动导入任务"
});

const imageAssets = computed(() =>
  gallery.assets
    .filter((asset) => asset.asset_type === "IMAGE" || asset.file_name.endsWith(".svg"))
    .map((asset) => ({ ...asset, previewUrl: previewUrl(asset.id) }))
);

// Lightbox图片列表
const lightboxImages = computed(() =>
  imageAssets.value.map((asset) => ({
    src: asset.previewUrl,
    alt: asset.file_name
  }))
);

const selectedMetaRows = computed(() => toSummaryRows(selectedAsset.value?.metadata || {}, 8));
const selectedInfoRows = computed(() =>
  toSummaryRows(
    {
      asset_type: selectedAsset.value?.asset_type,
      created_at: selectedAsset.value?.created_at,
      updated_at: selectedAsset.value?.updated_at,
      size: formatBytes(selectedAsset.value?.size_bytes),
      sha256: shortenText(selectedAsset.value?.sha256, 12, 8)
    },
    8
  )
);

function previewUrl(assetId) {
  const key = String(assetId);
  if (blobCache.value[key]) return blobCache.value[key];
  getCachedBlob(key, () => authFetchBlob(`/api/assets/${assetId}/download`)).catch(() => {});
  return "";
}

async function loadAssets() {
  await gallery.fetchAssets();
  if (selectedAsset.value && !gallery.assets.some((item) => item.id === selectedAsset.value.id)) {
    selectedAsset.value = null;
  }
}

async function loadMeta() {
  try {
    const [taskList, robotList] = await Promise.all([
      tasksApi.list({ page: 1, page_size: 100 }),
      robotsApi.list({ page: 1, page_size: 100 })
    ]);
    tasks.value = taskList.items;
    robots.value = robotList.items;
    if (!importForm.robot_id && robotList.items.length) {
      importForm.robot_id = robotList.items[0].id;
    }
  } catch (err) {
    gallery.error = err.message;
  }
}

async function openAsset(assetId) {
  assetLoading.value = true;
  try {
    selectedAsset.value = await assetsApi.get(assetId);
  } catch (err) {
    gallery.error = err.message;
    showError("加载失败", err.message);
  } finally {
    assetLoading.value = false;
  }
}

// 打开Lightbox
function openLightbox(assetId) {
  const index = imageAssets.value.findIndex((a) => a.id === assetId);
  if (index >= 0) {
    lightboxIndex.value = index;
    lightboxVisible.value = true;
  }
}

function onFileChange(event) {
  uploadFiles.value = Array.from(event.target.files || []);
}

async function uploadRealFiles() {
  gallery.error = "";
  uploading.value = true;
  uploadCurrentIndex.value = 0;
  uploadCurrentProgress.value = 0;
  try {
    const robot = robots.value.find((item) => item.id === importForm.robot_id);
    if (!robot) {
      throw new Error("请先选择机器人");
    }
    if (!uploadFiles.value.length) {
      throw new Error("请先选择至少一个文件");
    }

    const task = await tasksApi.create({
      name: `${importForm.task_name}-${new Date().toLocaleTimeString()}`,
      task_type: "manual_image_import",
      robot_id: importForm.robot_id,
      priority: 2,
      parameters: { source: "manual-upload", file_count: uploadFiles.value.length }
    });
    await tasksApi.dispatch(task.id);

    const failedFiles = [];
    for (let index = 0; index < uploadFiles.value.length; index += 1) {
      const file = uploadFiles.value[index];
      uploadCurrentIndex.value = index;
      uploadCurrentProgress.value = 0;
      try {
        const session = await assetsApi.createUploadSession({
          task_id: task.id,
          asset_type: "IMAGE",
          file_name: file.name
        });
        const formData = new FormData();
        formData.append("file", file);
        await assetsApi.uploadContent(session.upload_session_id, formData, {
          onUploadProgress(event) {
            if (event.total) {
              uploadCurrentProgress.value = Math.round((event.loaded / event.total) * 100);
            }
          }
        });
        await assetsApi.completeUpload(session.upload_session_id, {
          metadata: {
            source: "manual-upload",
            original_name: file.name,
            robot_code: robot.robot_code
          },
          trigger_analysis: index === uploadFiles.value.length - 1
        });
      } catch (fileErr) {
        failedFiles.push({ name: file.name, error: fileErr.message });
      }
    }

    uploadFiles.value = [];
    await Promise.all([loadMeta(), loadAssets()]);

    if (failedFiles.length) {
      showError("部分上传失败", `${failedFiles.length} 个文件上传失败`);
      gallery.error = `${failedFiles.length} 个文件上传失败: ${failedFiles.map((f) => f.name).join(", ")}`;
    } else {
      showSuccess("上传完成", `成功上传 ${uploadFiles.value.length || '所有'} 个文件`);
    }
  } catch (err) {
    gallery.error = err.message;
    showError("上传失败", err.message);
  } finally {
    uploading.value = false;
  }
}

onMounted(async () => {
  await Promise.all([loadMeta(), loadAssets()]);
});
</script>

<template>
  <div ref="pageRef" class="page-grid">
    <SectionHero
      eyebrow="Data Gallery"
      title="采集数据图库"
      subtitle="查看入库资产并执行正式手动导入。"
      split
      data-reveal
    >
      <template #actions>
        <button
          class="btn secondary"
          @click="loadAssets"
          :disabled="gallery.loading"
          :class="{ loading: gallery.loading }"
        >
          <template v-if="!gallery.loading">刷新图库</template>
        </button>
        <button class="btn secondary" @click="railCollapsed = !railCollapsed">
          {{ railCollapsed ? "展开控制栏" : "收起控制栏" }}
        </button>
      </template>
      <template #aside>
        <div class="hero-kpis">
          <div class="hero-kpi">
            <span>图片资产</span>
            <strong>{{ imageAssets.length }}</strong>
          </div>
          <div class="hero-kpi">
            <span>任务筛选</span>
            <strong>{{ gallery.filters.task_id ? "已启用" : "全部" }}</strong>
          </div>
        </div>
      </template>
    </SectionHero>

    <p v-if="gallery.error" class="error-text" role="alert">{{ gallery.error }}</p>

    <section class="gallery-layout">
      <!-- 侧边控制栏 -->
      <aside v-show="!railCollapsed" class="gallery-rail sticky-column">
        <DataGalleryFilterPanel
          v-model:filters="filters"
          :tasks="tasks"
          :robots="robots"
          @refresh="loadAssets"
        />
        <UploadProgress
          :files="uploadFiles"
          :current-index="uploadCurrentIndex"
          :current-progress="uploadCurrentProgress"
          :visible="uploading"
        />
        <DataGalleryUploadPanel
          v-model:form="importForm"
          :robots="robots"
          :upload-count="uploadFiles.length"
          :uploading="uploading"
          @file-change="onFileChange"
          @submit="uploadRealFiles"
        />
      </aside>

      <div class="stack">
        <!-- 图片网格 -->
        <section class="glass-card" data-reveal-scroll>
          <div class="section-head">
            <div>
              <div class="eyebrow">Gallery</div>
              <h3>图片网格</h3>
              <p class="page-subtitle">点击卡片查看关联详情，双击放大查看。</p>
            </div>
            <StatusPill :label="`${imageAssets.length} 张`" />
          </div>

          <!-- 加载状态 -->
          <div v-if="gallery.loading" class="gallery-skeleton">
            <SkeletonBlock v-for="i in 8" :key="i" :lines="1" />
          </div>

          <!-- 图片网格 -->
          <GalleryGrid
            v-else-if="imageAssets.length"
            :items="imageAssets"
            :selected-id="selectedAsset?.id"
            @select="openAsset"
            @dblclick="openLightbox"
          />

          <!-- 空状态 -->
          <EmptyState
            v-else
            title="当前筛选下没有图片资产"
            description="导入真实文件后，这里会展示正式入库资产。"
          />
        </section>

        <!-- 资产详情 -->
        <section class="glass-card" data-reveal-scroll>
          <div class="section-head">
            <div>
              <div class="eyebrow">Asset Detail</div>
              <h3>资产详情</h3>
            </div>
            <button
              v-if="selectedAsset"
              class="btn secondary btn-sm"
              @click="openLightbox(selectedAsset.id)"
            >
              放大查看
            </button>
          </div>
          <AssetDetailPanel
            :asset="selectedAsset"
            :preview-url="previewUrl"
            :info-rows="selectedInfoRows"
            :meta-rows="selectedMetaRows"
          />
        </section>
      </div>
    </section>

    <!-- Lightbox查看器 -->
    <LightboxViewer
      v-model:visible="lightboxVisible"
      :images="lightboxImages"
      :initial-index="lightboxIndex"
    />
  </div>
</template>

<style scoped>
.gallery-skeleton {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: var(--space-4);
}
</style>
