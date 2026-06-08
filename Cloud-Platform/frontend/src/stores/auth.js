import { defineStore } from "pinia";

import http, {
  getAuthToken,
  getRefreshToken,
  setAuthToken,
  setRefreshToken,
  clearAuthToken
} from "../api/client";
import { isTokenExpired } from "../utils/token";

export const useAuthStore = defineStore("auth", {
  state: () => ({
    token: getAuthToken(),
    refreshToken: getRefreshToken(),
    user: null
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.token),
    isAdmin: (state) => state.user?.role?.name === "admin",
    isOperator: (state) => state.user?.role?.name === "operator"
  },
  actions: {
    setSession(data) {
      this.token = data.token;
      this.refreshToken = data.refresh_token;
      this.user = data.user;
      setAuthToken(data.token);
      if (data.refresh_token) {
        setRefreshToken(data.refresh_token);
      }
    },
    async login(username, password) {
      const data = await http.post("/auth/login", { username, password });
      this.setSession(data);
    },
    async bootstrapAdmin(username, password, bootstrapToken = "") {
      const headers = bootstrapToken ? { "X-Bootstrap-Token": bootstrapToken } : {};
      const data = await http.post("/auth/bootstrap-admin", { username, password }, { headers });
      this.setSession(data);
    },
    async tryRefreshToken() {
      const refreshToken = this.refreshToken;
      if (!refreshToken) return false;
      try {
        const data = await http.post("/auth/refresh", { refresh_token: refreshToken });
        this.token = data.token;
        this.refreshToken = data.refresh_token;
        setAuthToken(data.token);
        setRefreshToken(data.refresh_token);
        return true;
      } catch {
        return false;
      }
    },
    async restore() {
      if (!this.token) return;
      // If access token is expired, try to refresh before fetching /auth/me
      if (isTokenExpired(this.token)) {
        const refreshed = await this.tryRefreshToken();
        if (!refreshed) {
          this.token = null;
          this.refreshToken = null;
          this.user = null;
          clearAuthToken();
          return;
        }
      }
      this.user = await http.get("/auth/me");
    },
    async logout() {
      const refreshToken = this.refreshToken;
      this.token = null;
      this.refreshToken = null;
      this.user = null;
      clearAuthToken();
      // Notify server to revoke the refresh token
      if (refreshToken) {
        try {
          await http.post("/auth/logout", { refresh_token: refreshToken });
        } catch {
          // Ignore errors during logout
        }
      }
    }
  }
});
