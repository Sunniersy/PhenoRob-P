import { createRouter, createWebHistory } from "vue-router";

import MainLayout from "../layouts/MainLayout.vue";
import { getAuthToken } from "../api/client";
import { useAuthStore } from "../stores/auth";
import { isTokenExpired } from "../utils/token";

const routes = [
  { path: "/login", component: () => import("../views/LoginView.vue"), meta: { title: "登录" } },
  {
    path: "/",
    component: MainLayout,
    children: [
      { path: "", redirect: "/dashboard" },
      { path: "/dashboard", component: () => import("../views/DashboardView.vue"), meta: { title: "总览", section: "总览" } },
      { path: "/tasks/create", component: () => import("../views/TaskCreateView.vue"), meta: { title: "新建任务", section: "任务" } },
      { path: "/tasks", component: () => import("../views/TaskListView.vue"), meta: { title: "任务中心", section: "任务" } },
      { path: "/tasks/:id", component: () => import("../views/TaskDetailView.vue"), meta: { title: "任务详情", section: "任务" } },
      { path: "/robots", component: () => import("../views/RobotMonitorView.vue"), meta: { title: "设备控制", section: "设备" } },
      { path: "/data", component: () => import("../views/DataGalleryView.vue"), meta: { title: "采集图库", section: "图库" } },
      { path: "/results", component: () => import("../views/ResultQueryView.vue"), meta: { title: "结果中心", section: "结果" } },
      { path: "/admin", component: () => import("../views/AdminView.vue"), meta: { title: "系统管理", section: "管理", requiresAdmin: true } }
    ]
  },
  { path: "/:pathMatch(.*)*", redirect: "/dashboard" }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

router.beforeEach(async (to) => {
  const token = getAuthToken();

  // Redirect to login if accessing a protected route without a token
  if (to.path !== "/login" && !token) {
    return "/login";
  }

  // If token exists, validate it before allowing navigation
  if (token && to.path !== "/login") {
    if (isTokenExpired(token)) {
      // Token expired: attempt silent refresh
      const authStore = useAuthStore();
      const refreshed = await authStore.tryRefreshToken();
      if (!refreshed) {
        return "/login";
      }
    }
  }

  // Redirect authenticated users away from the login page
  if (to.path === "/login" && getAuthToken()) {
    return "/dashboard";
  }

  // Role-based access control for admin-only routes
  if (to.meta.requiresAdmin) {
    const authStore = useAuthStore();
    if (!authStore.user) {
      try {
        await authStore.restore();
      } catch {
        return "/login";
      }
    }
    if (authStore.user && !authStore.isAdmin) {
      return "/dashboard";
    }
  }

  return true;
});

const APP_TITLE = "PhenoBot Cloud";
router.afterEach((to) => {
  const page = to.meta?.title;
  document.title = page ? `${page} - ${APP_TITLE}` : APP_TITLE;
});

export default router;
