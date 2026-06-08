import { ref, onMounted, onUnmounted } from "vue";

// 快捷键注册表
const shortcuts = ref([]);

// 注册快捷键
function registerShortcut(key, callback, description = "") {
  const shortcut = {
    id: Date.now() + Math.random(),
    key,
    callback,
    description
  };
  shortcuts.value.push(shortcut);
  return shortcut.id;
}

// 注销快捷键
function unregisterShortcut(id) {
  shortcuts.value = shortcuts.value.filter((s) => s.id !== id);
}

// 解析快捷键字符串
function parseKey(keyStr) {
  const parts = keyStr.toLowerCase().split("+");
  const key = {
    ctrl: false,
    meta: false,
    shift: false,
    alt: false,
    key: ""
  };

  parts.forEach((part) => {
    switch (part) {
      case "ctrl":
      case "control":
        key.ctrl = true;
        break;
      case "cmd":
      case "meta":
        key.meta = true;
        break;
      case "shift":
        key.shift = true;
        break;
      case "alt":
      case "option":
        key.alt = true;
        break;
      default:
        key.key = part;
    }
  });

  return key;
}

// 匹配快捷键
function matchKey(event, keyStr) {
  const key = parseKey(keyStr);

  // 检查修饰键
  if (key.ctrl && !event.ctrlKey) return false;
  if (key.meta && !event.metaKey) return false;
  if (key.shift && !event.shiftKey) return false;
  if (key.alt && !event.altKey) return false;

  // 检查主键
  const eventKey = event.key.toLowerCase();
  const targetKey = key.key.toLowerCase();

  // 特殊键映射
  const keyMap = {
    enter: "enter",
    return: "enter",
    escape: "escape",
    esc: "escape",
    tab: "tab",
    space: " ",
    backspace: "backspace",
    delete: "delete",
    del: "delete",
    up: "arrowup",
    down: "arrowdown",
    left: "arrowleft",
    right: "arrowright",
    home: "home",
    end: "end",
    pageup: "pageup",
    pagedown: "pagedown"
  };

  const mappedKey = keyMap[targetKey] || targetKey;
  return eventKey === mappedKey;
}

// 全局键盘事件处理
function handleKeydown(event) {
  // 忽略输入框中的快捷键
  const tagName = event.target.tagName.toLowerCase();
  if (tagName === "input" || tagName === "textarea" || tagName === "select") {
    // 只处理Escape键
    if (event.key !== "Escape") return;
  }

  // 遍历所有注册的快捷键
  for (const shortcut of shortcuts.value) {
    if (matchKey(event, shortcut.key)) {
      event.preventDefault();
      event.stopPropagation();
      shortcut.callback(event);
      break;
    }
  }
}

export function useKeyboardShortcuts() {
  onMounted(() => {
    document.addEventListener("keydown", handleKeydown);
  });

  onUnmounted(() => {
    document.removeEventListener("keydown", handleKeydown);
  });

  return {
    registerShortcut,
    unregisterShortcut,
    shortcuts
  };
}

// 预定义快捷键
export const SHORTCUTS = {
  // 导航
  GO_TO_DASHBOARD: "g+d",
  GO_TO_TASKS: "g+t",
  GO_TO_GALLERY: "g+g",
  GO_TO_RESULTS: "g+r",
  GO_TO_ROBOTS: "g+b",
  GO_TO_ADMIN: "g+a",

  // 操作
  CREATE_TASK: "c",
  REFRESH: "r",
  SEARCH: "/",
  COMMAND_PALETTE: "cmd+k",
  COMMAND_PALETTE_WINDOWS: "ctrl+k",

  // 通用
  CLOSE: "escape",
  SAVE: "cmd+s",
  SAVE_WINDOWS: "ctrl+s",
  UNDO: "cmd+z",
  UNDO_WINDOWS: "ctrl+z",
  REDO: "cmd+shift+z",
  REDO_WINDOWS: "ctrl+shift+z"
};

// 快捷键描述
export const SHORTCUT_DESCRIPTIONS = {
  [SHORTCUTS.GO_TO_DASHBOARD]: "跳转到总览",
  [SHORTCUTS.GO_TO_TASKS]: "跳转到任务",
  [SHORTCUTS.GO_TO_GALLERY]: "跳转到图库",
  [SHORTCUTS.GO_TO_RESULTS]: "跳转到结果",
  [SHORTCUTS.GO_TO_ROBOTS]: "跳转到设备",
  [SHORTCUTS.GO_TO_ADMIN]: "跳转到管理",
  [SHORTCUTS.CREATE_TASK]: "创建任务",
  [SHORTCUTS.REFRESH]: "刷新页面",
  [SHORTCUTS.SEARCH]: "搜索",
  [SHORTCUTS.COMMAND_PALETTE]: "命令面板",
  [SHORTCUTS.CLOSE]: "关闭",
  [SHORTCUTS.SAVE]: "保存",
  [SHORTCUTS.UNDO]: "撤销",
  [SHORTCUTS.REDO]: "重做"
};
