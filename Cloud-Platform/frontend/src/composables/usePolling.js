import { onBeforeUnmount, onMounted, ref } from "vue";

/**
 * 轮询 composable
 * @param {Function} callback - 轮询回调（支持 async）
 * @param {number} interval - 轮询间隔（毫秒），默认 30000
 * @returns {{ start: () => void, stop: () => void, isActive: import('vue').Ref<boolean> }}
 */
export function usePolling(callback, interval = 30000) {
  let timer = null;
  const isActive = ref(false);

  function start() {
    stop();
    isActive.value = true;
    timer = window.setInterval(async () => {
      try {
        await callback();
      } catch (err) {
        console.error("[usePolling] callback error:", err);
      }
    }, interval);
  }

  function stop() {
    if (timer !== null) {
      window.clearInterval(timer);
      timer = null;
    }
    isActive.value = false;
  }

  function handleVisibilityChange() {
    if (document.hidden) {
      stop();
    } else {
      callback().catch((err) => console.error("[usePolling] visibility callback error:", err));
      start();
    }
  }

  onMounted(() => {
    start();
    document.addEventListener("visibilitychange", handleVisibilityChange);
  });

  onBeforeUnmount(() => {
    stop();
    document.removeEventListener("visibilitychange", handleVisibilityChange);
  });

  return { start, stop, isActive };
}
