# PhenoBot Cloud Frontend

温室机器人云端控制台前端项目。

## 技术栈

- **框架**: Vue 3.4 + Vite 5
- **状态管理**: Pinia
- **路由**: Vue Router 4
- **HTTP客户端**: Axios
- **动画**: Motion (motion.dev)
- **测试**: Vitest + jsdom
- **代码规范**: ESLint 9 + eslint-plugin-vue

## 项目结构

```
frontend/
├── src/
│   ├── api/              # API层
│   │   ├── client.js     # Axios实例和拦截器
│   │   ├── index.js      # 统一导出
│   │   └── *.js          # 各模块API
│   ├── components/       # 组件
│   │   ├── BaseModal.vue
│   │   ├── ChartCard.vue
│   │   ├── CommandPalette.vue
│   │   ├── ErrorBoundary.vue
│   │   ├── GlobalSearch.vue
│   │   ├── LightboxViewer.vue
│   │   ├── NotificationCenter.vue
│   │   ├── ThemeToggle.vue
│   │   ├── ToastContainer.vue
│   │   └── ...
│   ├── composables/      # 组合式函数
│   │   ├── useAccessibility.js
│   │   ├── useBlobCache.js
│   │   ├── useExport.js
│   │   ├── useKeyboardShortcuts.js
│   │   ├── useMotionReveal.js
│   │   ├── usePolling.js
│   │   ├── usePreferences.js
│   │   ├── useTaskActions.js
│   │   ├── useTheme.js
│   │   └── useToast.js
│   ├── constants/        # 常量
│   │   └── taskStatus.js
│   ├── i18n/             # 国际化
│   │   └── index.js
│   ├── layouts/          # 布局
│   │   └── MainLayout.vue
│   ├── router/           # 路由
│   │   └── index.js
│   ├── services/         # 服务
│   │   └── ws.js
│   ├── stores/           # 状态管理
│   │   ├── auth.js
│   │   ├── dashboard.js
│   │   ├── notifications.js
│   │   └── ...
│   ├── styles/           # 样式
│   │   ├── tokens.css    # 设计token
│   │   ├── base.css      # 基础样式
│   │   ├── layout.css    # 布局样式
│   │   ├── components.css # 组件样式
│   │   └── pages.css     # 页面样式
│   ├── utils/            # 工具函数
│   │   ├── presenter.js
│   │   └── token.js
│   ├── views/            # 页面
│   │   ├── LoginView.vue
│   │   ├── DashboardView.vue
│   │   ├── TaskListView.vue
│   │   ├── TaskCreateView.vue
│   │   ├── TaskDetailView.vue
│   │   ├── RobotMonitorView.vue
│   │   ├── DataGalleryView.vue
│   │   ├── ResultQueryView.vue
│   │   └── AdminView.vue
│   ├── App.vue
│   ├── main.js
│   └── service-worker.js
├── index.html
├── package.json
├── vite.config.js
└── vitest.config.js
```

## 功能特性

### 设计系统
- 完整的设计token系统 (颜色、排版、间距、动画)
- 暗色/亮色主题切换
- 响应式布局 (移动端、平板、桌面)
- 无障碍支持 (高对比度、大字体、减少动画)

### 组件库
- 基础组件: 按钮、表单、卡片、表格、模态框
- 业务组件: 图表、时间线、状态标签、进度条
- 高级组件: 命令面板、全局搜索、通知中心、Lightbox

### 页面功能
- 登录/初始化: 双面板布局、表单验证
- 仪表板: 指标卡片、依赖检查、最近任务
- 任务管理: 创建、列表、详情、状态流转
- 设备监控: 设备列表、控制面板、命令历史
- 数据图库: 图片网格、筛选、上传、Lightbox
- 结果查询: 结果列表、下载、搜索
- 系统管理: 用户、设备、告警、系统状态

### 交互体验
- Toast通知系统
- 骨架屏加载
- 动画过渡 (页面、列表、模态框)
- 键盘快捷键 (Cmd+K命令面板)
- 搜索防抖 (400ms)

## 开发指南

### 安装依赖
```bash
npm install
```

### 开发模式
```bash
npm run dev
```

### 构建生产版本
```bash
npm run build
```

### 运行测试
```bash
npm run test
```

### 代码检查
```bash
npm run lint
```

## 设计规范

### 颜色系统
- 品牌色: #10a37f (绿色)
- 成功色: #22c55e
- 警告色: #f59e0b
- 危险色: #ef4444
- 信息色: #3b82f6

### 排版系统
- 字体: Inter, Noto Sans SC
- 字号: 11px - 48px
- 字重: 400 - 700
- 行高: 1.15 - 1.65

### 间距系统
- 基础单位: 4px
- 间距范围: 4px - 96px
- 语义间距: gap-xs, gap-sm, gap-md, gap-base, gap-lg, gap-xl, gap-2xl

### 动画系统
- 时长: 100ms - 500ms
- 缓动: ease, ease-out, ease-in, spring, bounce
- 工具类: fade-in, slide-up, scale-in, pulse, shake

## 快捷键

### 全局快捷键
- `Cmd+K` / `Ctrl+K`: 打开命令面板
- `Escape`: 关闭模态框/面板

### 导航快捷键
- `g+d`: 跳转到总览
- `g+t`: 跳转到任务
- `g+g`: 跳转到图库
- `g+r`: 跳转到结果
- `g+b`: 跳转到设备
- `g+a`: 跳转到管理

### 操作快捷键
- `c`: 创建任务
- `r`: 刷新页面
- `/`: 搜索

## 国际化

支持语言:
- 中文 (zh-CN)
- 英文 (en-US)

使用方式:
```javascript
import { t } from '@/i18n'

t('common.loading') // 加载中...
t('tasks.status.running') // 执行中
```

## 浏览器支持

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## 许可证

MIT License
