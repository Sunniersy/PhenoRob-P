<script setup>
import { onBeforeUnmount, ref, watch } from "vue";

import { authFetchBlob } from "../api/client";
import { useBlobCache } from "../composables/useBlobCache";

const props = defineProps({
  assetId: { type: String, required: true },
  alt: { type: String, default: "" },
  rootMargin: { type: String, default: "200px" }
});

const { get: getCachedBlob, cache: blobCache } = useBlobCache();
const imgRef = ref(null);
const src = ref("");
const isVisible = ref(false);
let observer = null;

function startObserver() {
  if (!imgRef.value || observer) return;
  observer = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          isVisible.value = true;
          observer.disconnect();
          observer = null;
          break;
        }
      }
    },
    { rootMargin: props.rootMargin, threshold: 0.01 }
  );
  observer.observe(imgRef.value);
}

async function loadBlob() {
  const key = String(props.assetId);
  if (blobCache.value[key]) {
    src.value = blobCache.value[key];
    return;
  }
  try {
    src.value = await getCachedBlob(key, () => authFetchBlob(`/api/assets/${props.assetId}/download`));
  } catch {
    /* ignore */
  }
}

watch(isVisible, (visible) => {
  if (visible) loadBlob();
});

watch(
  () => props.assetId,
  () => {
    src.value = "";
    if (isVisible.value) loadBlob();
  }
);

import { onMounted } from "vue";

onMounted(startObserver);

onBeforeUnmount(() => {
  if (observer) {
    observer.disconnect();
    observer = null;
  }
});
</script>

<template>
  <img ref="imgRef" :src="src" :alt="alt" loading="lazy" />
</template>
