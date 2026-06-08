import { onBeforeUnmount, ref } from "vue";

/**
 * Blob URL 缓存 composable（LRU 策略）
 * @param {Object} options
 * @param {number} options.maxSize - 最大缓存数量，默认 50
 * @returns {{ get: (key: string, fetcher: () => Promise<Blob>) => Promise<string>, preload: (keys: string[], fetcher: (key: string) => Promise<Blob>) => Promise<void>, revokeAll: () => void, cache: import('vue').Ref<Record<string, string>> }}
 */
export function useBlobCache({ maxSize = 50 } = {}) {
  /** @type {Map<string, string>} key -> Object URL, 维护访问顺序 */
  const lruMap = new Map();
  /** 用于模板响应式绑定 */
  const cache = ref({});

  function syncRef() {
    cache.value = Object.fromEntries(lruMap);
  }

  /**
   * 将 key 移到最新位置（标记为最近使用）
   */
  function touch(key) {
    const url = lruMap.get(key);
    if (url !== undefined) {
      lruMap.delete(key);
      lruMap.set(key, url);
      syncRef();
    }
  }

  /**
   * 淘汰最久未使用的条目
   */
  function evict() {
    while (lruMap.size > maxSize) {
      const [oldestKey, oldestUrl] = lruMap.entries().next().value;
      lruMap.delete(oldestKey);
      try {
        URL.revokeObjectURL(oldestUrl);
      } catch {
        /* ignore */
      }
    }
    syncRef();
  }

  /**
   * 获取缓存的 Object URL，若不存在则调用 fetcher 加载
   * @param {string} key - 缓存键（如 asset ID）
   * @param {() => Promise<Blob>} fetcher - 获取 Blob 的异步函数
   * @returns {Promise<string>} Object URL
   */
  async function get(key, fetcher) {
    if (lruMap.has(key)) {
      touch(key);
      return lruMap.get(key);
    }

    const blob = await fetcher();
    const url = URL.createObjectURL(blob);
    lruMap.set(key, url);
    evict();
    return url;
  }

  /**
   * 批量预加载
   * @param {string[]} keys - 要预加载的 key 列表
   * @param {(key: string) => Promise<Blob>} fetcher - 根据 key 获取 Blob 的函数
   */
  async function preload(keys, fetcher) {
    await Promise.allSettled(
      keys
        .filter((key) => !lruMap.has(key))
        .map(async (key) => {
          try {
            const blob = await fetcher(key);
            const url = URL.createObjectURL(blob);
            lruMap.set(key, url);
          } catch (err) {
            console.warn(`[useBlobCache] preload failed for ${key}:`, err);
          }
        })
    );
    evict();
  }

  /**
   * 释放所有缓存的 Object URL
   */
  function revokeAll() {
    for (const url of lruMap.values()) {
      try {
        URL.revokeObjectURL(url);
      } catch {
        /* ignore */
      }
    }
    lruMap.clear();
    syncRef();
  }

  onBeforeUnmount(() => {
    revokeAll();
  });

  return { get, preload, revokeAll, cache };
}
