import { ref, watch, onMounted } from "vue";

const STORAGE_KEY = "phenobot-preferences";

// 默认偏好设置
const defaultPreferences = {
  theme: "system", // light, dark, system
  language: "zh-CN", // zh-CN, en-US
  sidebarCollapsed: false,
  pageSize: 10,
  dateFormat: "YYYY-MM-DD",
  timeFormat: "24h", // 12h, 24h
  notifications: {
    enabled: true,
    sound: false,
    desktop: false
  },
  table: {
    density: "normal", // compact, normal, relaxed
    showGridLines: true
  },
  chart: {
    animation: true,
    showLabels: true
  }
};

// 当前偏好设置
const preferences = ref({ ...defaultPreferences });

// 从localStorage加载偏好
function loadPreferences() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      const parsed = JSON.parse(saved);
      preferences.value = { ...defaultPreferences, ...parsed };
    }
  } catch (err) {
    console.error("Failed to load preferences:", err);
  }
}

// 保存偏好到localStorage
function savePreferences() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(preferences.value));
  } catch (err) {
    console.error("Failed to save preferences:", err);
  }
}

// 更新偏好
function updatePreference(key, value) {
  const keys = key.split(".");
  let obj = preferences.value;

  for (let i = 0; i < keys.length - 1; i++) {
    if (!obj[keys[i]]) {
      obj[keys[i]] = {};
    }
    obj = obj[keys[i]];
  }

  obj[keys[keys.length - 1]] = value;
  savePreferences();
}

// 重置偏好
function resetPreferences() {
  preferences.value = { ...defaultPreferences };
  savePreferences();
}

// 获取偏好
function getPreference(key, defaultValue = null) {
  const keys = key.split(".");
  let obj = preferences.value;

  for (const k of keys) {
    if (obj && typeof obj === "object" && k in obj) {
      obj = obj[k];
    } else {
      return defaultValue;
    }
  }

  return obj;
}

// 应用主题
function applyTheme(theme) {
  const html = document.documentElement;

  if (theme === "system") {
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    html.setAttribute("data-theme", prefersDark ? "dark" : "light");
  } else {
    html.setAttribute("data-theme", theme);
  }

  localStorage.setItem("phenobot-theme", theme);
}

// 应用语言
function applyLanguage(language) {
  document.documentElement.lang = language;
  localStorage.setItem("phenobot-language", language);
}

// 监听系统主题变化
function watchSystemTheme() {
  const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
  mediaQuery.addEventListener("change", () => {
    if (preferences.value.theme === "system") {
      applyTheme("system");
    }
  });
}

export function usePreferences() {
  onMounted(() => {
    loadPreferences();
    applyTheme(preferences.value.theme);
    applyLanguage(preferences.value.language);
    watchSystemTheme();
  });

  // 监听主题变化
  watch(
    () => preferences.value.theme,
    (newTheme) => {
      applyTheme(newTheme);
    }
  );

  // 监听语言变化
  watch(
    () => preferences.value.language,
    (newLanguage) => {
      applyLanguage(newLanguage);
    }
  );

  return {
    preferences,
    updatePreference,
    resetPreferences,
    getPreference,
    defaultPreferences
  };
}
