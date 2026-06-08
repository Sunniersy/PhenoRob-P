import axios from "axios";

const TOKEN_KEY = "phenobot-token";
const REFRESH_TOKEN_KEY = "phenobot-refresh-token";

const http = axios.create({
  baseURL: "/api",
  timeout: 10000
});

let onUnauthorized = null;
let isRefreshing = false;
let failedQueue = [];

function processQueue(error, token) {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
}

export function getAuthToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setAuthToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearAuthToken() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

export function getRefreshToken() {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function setRefreshToken(token) {
  localStorage.setItem(REFRESH_TOKEN_KEY, token);
}

export function clearRefreshToken() {
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

export async function authFetchBlob(url) {
  // Extract the resource path (before query params) for token binding
  const [resourcePath, existingQuery] = url.split("?");
  const token = getAuthToken();

  // Exchange JWT for a one-time download token
  const dlResp = await fetch("/api/downloads/token", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    },
    body: JSON.stringify({ path: resourcePath })
  });
  if (!dlResp.ok) throw new Error(`获取下载令牌失败: ${dlResp.status}`);
  const { dl_token } = (await dlResp.json()).data;

  // Build download URL with one-time token
  const params = new URLSearchParams(existingQuery || "");
  params.set("dl_token", dl_token);
  const secureUrl = `${resourcePath}?${params.toString()}`;

  const response = await fetch(secureUrl);
  if (!response.ok) throw new Error(`请求失败: ${response.status}`);
  return response.blob();
}

export async function authFetchBlobUrl(url) {
  const blob = await authFetchBlob(url);
  return URL.createObjectURL(blob);
}

http.interceptors.request.use((config) => {
  const token = getAuthToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

http.interceptors.response.use(
  (response) => response.data.data,
  (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      const refreshToken = getRefreshToken();
      if (!refreshToken) {
        clearAuthToken();
        onUnauthorized?.();
        return Promise.reject(new Error("会话已过期，请重新登录"));
      }

      // Avoid infinite loop on the refresh endpoint itself
      if (originalRequest.url === "/auth/refresh") {
        clearAuthToken();
        onUnauthorized?.();
        return Promise.reject(new Error("会话已过期，请重新登录"));
      }

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`;
          return http(originalRequest);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      return new Promise((resolve, reject) => {
        axios
          .post("/api/auth/refresh", { refresh_token: refreshToken }, { timeout: 10000 })
          .then((resp) => {
            const data = resp.data.data;
            setAuthToken(data.token);
            setRefreshToken(data.refresh_token);
            originalRequest.headers.Authorization = `Bearer ${data.token}`;
            processQueue(null, data.token);
            resolve(http(originalRequest));
          })
          .catch((refreshError) => {
            processQueue(refreshError, null);
            clearAuthToken();
            onUnauthorized?.();
            reject(new Error("会话已过期，请重新登录"));
          })
          .finally(() => {
            isRefreshing = false;
          });
      });
    }

    const message =
      error.response?.status === 403
        ? "当前账号没有权限执行该操作"
        : error.response?.data?.message || error.message;
    return Promise.reject(new Error(message));
  }
);

export function setUnauthorizedHandler(handler) {
  onUnauthorized = handler;
}

export default http;
