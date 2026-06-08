import { ref, onMounted, onUnmounted } from "vue";

// 无障碍配置
const config = {
  // 高对比度模式
  highContrast: false,
  // 大字体模式
  largeText: false,
  // 减少动画
  reduceMotion: false,
  // 屏幕阅读器优化
  screenReader: false,
  // 键盘导航
  keyboardNavigation: true
};

// 无障碍状态
const accessibility = ref({ ...config });

// 检测系统偏好
function detectSystemPreferences() {
  // 检测减少动画偏好
  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  accessibility.value.reduceMotion = prefersReducedMotion.matches;

  // 检测高对比度偏好
  const prefersHighContrast = window.matchMedia("(prefers-contrast: high)");
  accessibility.value.highContrast = prefersHighContrast.matches;

  // 监听变化
  prefersReducedMotion.addEventListener("change", (e) => {
    accessibility.value.reduceMotion = e.matches;
    applyAccessibility();
  });

  prefersHighContrast.addEventListener("change", (e) => {
    accessibility.value.highContrast = e.matches;
    applyAccessibility();
  });
}

// 应用无障碍设置
function applyAccessibility() {
  const html = document.documentElement;

  // 高对比度模式
  if (accessibility.value.highContrast) {
    html.classList.add("high-contrast");
  } else {
    html.classList.remove("high-contrast");
  }

  // 大字体模式
  if (accessibility.value.largeText) {
    html.classList.add("large-text");
  } else {
    html.classList.remove("large-text");
  }

  // 减少动画
  if (accessibility.value.reduceMotion) {
    html.classList.add("reduce-motion");
  } else {
    html.classList.remove("reduce-motion");
  }

  // 屏幕阅读器优化
  if (accessibility.value.screenReader) {
    html.classList.add("screen-reader");
  } else {
    html.classList.remove("screen-reader");
  }

  // 保存到localStorage
  localStorage.setItem("phenobot-accessibility", JSON.stringify(accessibility.value));
}

// 加载无障碍设置
function loadAccessibility() {
  try {
    const saved = localStorage.getItem("phenobot-accessibility");
    if (saved) {
      const parsed = JSON.parse(saved);
      accessibility.value = { ...config, ...parsed };
    }
  } catch (err) {
    console.error("Failed to load accessibility settings:", err);
  }
}

// 更新无障碍设置
function updateAccessibility(key, value) {
  accessibility.value[key] = value;
  applyAccessibility();
}

// 重置无障碍设置
function resetAccessibility() {
  accessibility.value = { ...config };
  applyAccessibility();
}

// 跳转到主内容
function skipToMainContent() {
  const mainContent = document.getElementById("main-content") || document.querySelector("main");
  if (mainContent) {
    mainContent.focus();
    mainContent.scrollIntoView({ behavior: "smooth" });
  }
}

// 跳转到导航
function skipToNavigation() {
  const navigation = document.getElementById("navigation") || document.querySelector("nav");
  if (navigation) {
    navigation.focus();
    navigation.scrollIntoView({ behavior: "smooth" });
  }
}

// 宣布消息给屏幕阅读器
function announceMessage(message, priority = "polite") {
  const announcer = document.getElementById("accessibility-announcer") || createAnnouncer();
  announcer.setAttribute("aria-live", priority);
  announcer.textContent = message;

  // 清空后重新设置，确保屏幕阅读器能检测到变化
  setTimeout(() => {
    announcer.textContent = "";
    setTimeout(() => {
      announcer.textContent = message;
    }, 100);
  }, 100);
}

// 创建消息宣布器
function createAnnouncer() {
  const announcer = document.createElement("div");
  announcer.id = "accessibility-announcer";
  announcer.setAttribute("aria-live", "polite");
  announcer.setAttribute("aria-atomic", "true");
  announcer.className = "visually-hidden";
  document.body.appendChild(announcer);
  return announcer;
}

// 键盘导航处理
function handleKeydown(event) {
  // Tab键导航
  if (event.key === "Tab") {
    document.body.classList.add("keyboard-navigation");
  }

  // Escape键关闭模态框
  if (event.key === "Escape") {
    const modals = document.querySelectorAll('[role="dialog"]');
    if (modals.length > 0) {
      const lastModal = modals[modals.length - 1];
      const closeButton = lastModal.querySelector("[aria-label='close'], [aria-label='关闭']");
      if (closeButton) {
        closeButton.click();
      }
    }
  }
}

// 鼠标导航处理
function handleMousedown() {
  document.body.classList.remove("keyboard-navigation");
}

export function useAccessibility() {
  onMounted(() => {
    loadAccessibility();
    detectSystemPreferences();
    applyAccessibility();

    document.addEventListener("keydown", handleKeydown);
    document.addEventListener("mousedown", handleMousedown);
  });

  onUnmounted(() => {
    document.removeEventListener("keydown", handleKeydown);
    document.removeEventListener("mousedown", handleMousedown);
  });

  return {
    accessibility,
    updateAccessibility,
    resetAccessibility,
    skipToMainContent,
    skipToNavigation,
    announceMessage
  };
}
