import { onBeforeUnmount, ref } from "vue";

/**
 * IntersectionObserver 懒加载 composable
 * @param {Object} options
 * @param {string} options.rootMargin - 预加载边距，默认 "200px"
 * @param {number} options.threshold - 可见度阈值，默认 0.1
 * @returns {{ observe: (el: Element, key: string) => void, unobserve: (el: Element) => void, visibleKeys: import('vue').Ref<Set<string>> }}
 */
export function useLazyLoad({ rootMargin = "200px", threshold = 0.1 } = {}) {
  const visibleKeys = ref(new Set());
  /** @type {Map<Element, string>} */
  const elementKeyMap = new Map();

  const observer = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        const key = elementKeyMap.get(entry.target);
        if (!key) continue;
        if (entry.isIntersecting) {
          visibleKeys.value.add(key);
          visibleKeys.value = new Set(visibleKeys.value);
        }
      }
    },
    { rootMargin, threshold }
  );

  function observe(el, key) {
    if (!el) return;
    elementKeyMap.set(el, key);
    observer.observe(el);
  }

  function unobserve(el) {
    if (!el) return;
    const key = elementKeyMap.get(el);
    if (key) {
      visibleKeys.value.delete(key);
      visibleKeys.value = new Set(visibleKeys.value);
    }
    elementKeyMap.delete(el);
    observer.unobserve(el);
  }

  onBeforeUnmount(() => {
    observer.disconnect();
    elementKeyMap.clear();
    visibleKeys.value = new Set();
  });

  return { observe, unobserve, visibleKeys };
}
