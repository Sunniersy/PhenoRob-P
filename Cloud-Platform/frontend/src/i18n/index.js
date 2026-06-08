// 国际化配置
const messages = {
  "zh-CN": {
    // 通用
    common: {
      loading: "加载中...",
      error: "错误",
      success: "成功",
      warning: "警告",
      info: "信息",
      confirm: "确认",
      cancel: "取消",
      save: "保存",
      delete: "删除",
      edit: "编辑",
      create: "创建",
      search: "搜索",
      refresh: "刷新",
      back: "返回",
      next: "下一步",
      previous: "上一步",
      submit: "提交",
      close: "关闭",
      yes: "是",
      no: "否",
      ok: "确定",
      apply: "应用",
      reset: "重置",
      export: "导出",
      import: "导入",
      download: "下载",
      upload: "上传",
      filter: "筛选",
      sort: "排序",
      view: "查看",
      details: "详情",
      more: "更多",
      less: "收起",
      all: "全部",
      none: "无",
      selected: "已选择",
      total: "总计",
      page: "页",
      of: "共",
      items: "条",
      noData: "暂无数据",
      noResults: "没有找到结果",
      retry: "重试",
      logout: "退出登录",
      login: "登录",
      register: "注册",
      username: "用户名",
      password: "密码",
      email: "邮箱",
      role: "角色",
      status: "状态",
      actions: "操作",
      createdAt: "创建时间",
      updatedAt: "更新时间",
      createdBy: "创建者",
      description: "描述",
      name: "名称",
      type: "类型",
      value: "值",
      key: "键",
      priority: "优先级",
      progress: "进度",
      message: "消息"
    },

    // 导航
    nav: {
      dashboard: "总览",
      tasks: "任务",
      gallery: "图库",
      results: "结果",
      robots: "设备",
      admin: "管理",
      createTask: "创建任务",
      taskDetail: "任务详情",
      robotControl: "设备控制",
      systemAdmin: "系统管理"
    },

    // 仪表板
    dashboard: {
      title: "农业设备云端运营总览",
      subtitle: "汇总设备、任务、资产与系统就绪状态。",
      systemReady: "系统就绪",
      systemDegraded: "依赖异常",
      onlineDevices: "在线设备",
      dependencyCheck: "依赖检查",
      runningTasks: "执行任务",
      activeAlerts: "活跃告警",
      recentTasks: "最近任务",
      recentAssets: "最近采集资产",
      alertsAndResults: "告警与结果"
    },

    // 任务
    tasks: {
      title: "任务中心",
      subtitle: "查看任务状态并继续调度。",
      create: "创建任务",
      list: "任务列表",
      detail: "任务详情",
      status: {
        draft: "草稿",
        pending: "待下发",
        dispatched: "已下发",
        acked: "已确认",
        running: "执行中",
        uploading: "上传中",
        ready: "数据就绪",
        analyzing: "分析中",
        completed: "已完成",
        failed: "失败",
        cancelling: "取消中",
        cancelled: "已取消"
      },
      actions: {
        dispatch: "下发",
        retry: "重试",
        cancel: "取消",
        view: "查看详情"
      }
    },

    // 设备
    robots: {
      title: "机器人控制台",
      subtitle: "查看设备状态并下发控制命令。",
      list: "设备列表",
      control: "控制面板",
      commands: "命令历史",
      status: {
        online: "在线",
        offline: "离线",
        charging: "充电中",
        moving: "移动中",
        idle: "空闲"
      },
      actions: {
        startCharge: "开始充电",
        stopCharge: "停止充电",
        returnHome: "返航/回桩",
        resumeTask: "继续任务",
        pauseTask: "暂停任务",
        cancelTask: "取消任务",
        captureImage: "触发采集拍照"
      }
    },

    // 图库
    gallery: {
      title: "采集数据图库",
      subtitle: "查看入库资产并执行正式手动导入。",
      filter: "筛选",
      upload: "上传",
      grid: "图片网格",
      detail: "资产详情"
    },

    // 结果
    results: {
      title: "结果中心",
      subtitle: "查看分析摘要、关联任务和结果文件。",
      list: "结果列表",
      download: "下载结果"
    },

    // 管理
    admin: {
      title: "系统管理",
      subtitle: "管理用户、设备与系统状态。",
      users: "用户管理",
      robots: "设备管理",
      alerts: "告警管理",
      system: "系统状态"
    },

    // 登录
    login: {
      title: "温室机器人云端控制台",
      subtitle: "任务、采集、设备与系统管理统一入口。",
      signIn: "登录",
      bootstrap: "初始化",
      username: "用户名",
      password: "密码",
      bootstrapToken: "初始化令牌",
      submit: "进入控制台",
      initializing: "初始化中...",
      checking: "检查系统状态..."
    }
  },

  "en-US": {
    // Common
    common: {
      loading: "Loading...",
      error: "Error",
      success: "Success",
      warning: "Warning",
      info: "Info",
      confirm: "Confirm",
      cancel: "Cancel",
      save: "Save",
      delete: "Delete",
      edit: "Edit",
      create: "Create",
      search: "Search",
      refresh: "Refresh",
      back: "Back",
      next: "Next",
      previous: "Previous",
      submit: "Submit",
      close: "Close",
      yes: "Yes",
      no: "No",
      ok: "OK",
      apply: "Apply",
      reset: "Reset",
      export: "Export",
      import: "Import",
      download: "Download",
      upload: "Upload",
      filter: "Filter",
      sort: "Sort",
      view: "View",
      details: "Details",
      more: "More",
      less: "Less",
      all: "All",
      none: "None",
      selected: "Selected",
      total: "Total",
      page: "Page",
      of: "of",
      items: "items",
      noData: "No data",
      noResults: "No results found",
      retry: "Retry",
      logout: "Logout",
      login: "Login",
      register: "Register",
      username: "Username",
      password: "Password",
      email: "Email",
      role: "Role",
      status: "Status",
      actions: "Actions",
      createdAt: "Created At",
      updatedAt: "Updated At",
      createdBy: "Created By",
      description: "Description",
      name: "Name",
      type: "Type",
      value: "Value",
      key: "Key",
      priority: "Priority",
      progress: "Progress",
      message: "Message"
    },

    // Navigation
    nav: {
      dashboard: "Dashboard",
      tasks: "Tasks",
      gallery: "Gallery",
      results: "Results",
      robots: "Robots",
      admin: "Admin",
      createTask: "Create Task",
      taskDetail: "Task Detail",
      robotControl: "Robot Control",
      systemAdmin: "System Admin"
    },

    // Dashboard
    dashboard: {
      title: "Agricultural Equipment Cloud Operations Overview",
      subtitle: "Summary of equipment, tasks, assets, and system readiness.",
      systemReady: "System Ready",
      systemDegraded: "Dependencies Degraded",
      onlineDevices: "Online Devices",
      dependencyCheck: "Dependency Check",
      runningTasks: "Running Tasks",
      activeAlerts: "Active Alerts",
      recentTasks: "Recent Tasks",
      recentAssets: "Recent Assets",
      alertsAndResults: "Alerts & Results"
    },

    // Tasks
    tasks: {
      title: "Task Center",
      subtitle: "View task status and continue scheduling.",
      create: "Create Task",
      list: "Task List",
      detail: "Task Detail",
      status: {
        draft: "Draft",
        pending: "Pending",
        dispatched: "Dispatched",
        acked: "Acknowledged",
        running: "Running",
        uploading: "Uploading",
        ready: "Data Ready",
        analyzing: "Analyzing",
        completed: "Completed",
        failed: "Failed",
        cancelling: "Cancelling",
        cancelled: "Cancelled"
      },
      actions: {
        dispatch: "Dispatch",
        retry: "Retry",
        cancel: "Cancel",
        view: "View Details"
      }
    },

    // Robots
    robots: {
      title: "Robot Console",
      subtitle: "View device status and send control commands.",
      list: "Device List",
      control: "Control Panel",
      commands: "Command History",
      status: {
        online: "Online",
        offline: "Offline",
        charging: "Charging",
        moving: "Moving",
        idle: "Idle"
      },
      actions: {
        startCharge: "Start Charge",
        stopCharge: "Stop Charge",
        returnHome: "Return Home",
        resumeTask: "Resume Task",
        pauseTask: "Pause Task",
        cancelTask: "Cancel Task",
        captureImage: "Capture Image"
      }
    },

    // Gallery
    gallery: {
      title: "Data Gallery",
      subtitle: "View imported assets and perform manual imports.",
      filter: "Filter",
      upload: "Upload",
      grid: "Image Grid",
      detail: "Asset Detail"
    },

    // Results
    results: {
      title: "Results Center",
      subtitle: "View analysis summaries, associated tasks, and result files.",
      list: "Results List",
      download: "Download Results"
    },

    // Admin
    admin: {
      title: "System Admin",
      subtitle: "Manage users, devices, and system status.",
      users: "User Management",
      robots: "Device Management",
      alerts: "Alert Management",
      system: "System Status"
    },

    // Login
    login: {
      title: "Greenhouse Robotics Cloud Console",
      subtitle: "Unified entry for tasks, collection, devices, and system management.",
      signIn: "Sign In",
      bootstrap: "Bootstrap",
      username: "Username",
      password: "Password",
      bootstrapToken: "Bootstrap Token",
      submit: "Enter Console",
      initializing: "Initializing...",
      checking: "Checking system status..."
    }
  }
};

// 当前语言
let currentLocale = localStorage.getItem("phenobot-language") || "zh-CN";

// 获取消息
function getMessage(key, locale = currentLocale) {
  const keys = key.split(".");
  let obj = messages[locale] || messages["zh-CN"];

  for (const k of keys) {
    if (obj && typeof obj === "object" && k in obj) {
      obj = obj[k];
    } else {
      return key; // 返回键作为默认值
    }
  }

  return obj;
}

// 设置语言
function setLocale(locale) {
  if (messages[locale]) {
    currentLocale = locale;
    localStorage.setItem("phenobot-language", locale);
    document.documentElement.lang = locale;
  }
}

// 获取当前语言
function getLocale() {
  return currentLocale;
}

// 获取支持的语言列表
function getSupportedLocales() {
  return Object.keys(messages);
}

// 翻译函数
function t(key, params = {}) {
  let message = getMessage(key);

  // 替换参数
  if (typeof message === "string") {
    Object.entries(params).forEach(([key, value]) => {
      message = message.replace(`{${key}}`, value);
    });
  }

  return message;
}

export { messages, getMessage, setLocale, getLocale, getSupportedLocales, t };
