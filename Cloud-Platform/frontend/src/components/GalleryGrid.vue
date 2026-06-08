<script setup>
import StatusPill from "./StatusPill.vue";

defineProps({
  items: { type: Array, default: () => [] },
  selectedId: { type: String, default: "" }
});

const emit = defineEmits(["select"]);
</script>

<template>
  <div class="gallery-grid">
    <article
      v-for="asset in items"
      :key="asset.id"
      class="asset-card"
      :class="{ active: asset.id === selectedId }"
      data-reveal-scroll
    >
      <button class="asset-card-button" type="button" @click="emit('select', asset.id)">
        <div class="asset-thumb-wrap">
          <img class="asset-thumb" :src="asset.previewUrl" :alt="asset.file_name" />
        </div>
        <div class="asset-card-body">
          <strong>{{ asset.file_name }}</strong>
          <div class="asset-card-meta">
            <span>{{ asset.robot_name || asset.robot_code || "-" }}</span>
            <span>{{ asset.created_at }}</span>
          </div>
          <StatusPill :label="asset.asset_type" />
        </div>
      </button>
    </article>
  </div>
</template>
