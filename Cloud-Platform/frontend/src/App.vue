<script setup>
import { ref, onMounted } from "vue";
import { RouterView } from "vue-router";
import ErrorBoundary from "./components/ErrorBoundary.vue";
import ToastContainer from "./components/ToastContainer.vue";
import { useTheme } from "./composables/useTheme";
import { useToast } from "./composables/useToast";

const { initTheme } = useTheme();
const { setRef } = useToast();
const toastRef = ref(null);

onMounted(() => {
  initTheme();
  if (toastRef.value) {
    setRef(toastRef.value);
  }
});
</script>

<template>
  <ErrorBoundary>
    <RouterView v-slot="{ Component }">
      <transition name="route-fade" mode="out-in">
        <component :is="Component" />
      </transition>
    </RouterView>
    <ToastContainer ref="toastRef" />
  </ErrorBoundary>
</template>
