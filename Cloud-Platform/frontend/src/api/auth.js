import http from "./client";

/**
 * Auth API
 *
 * Centralized authentication endpoints. The http client interceptor
 * already unwraps response.data.data and handles token refresh,
 * so these functions return the inner payload directly.
 */

export async function login(username, password) {
  return http.post("/auth/login", { username, password });
}

export async function bootstrapAdmin(username, password, bootstrapToken = "") {
  const headers = bootstrapToken ? { "X-Bootstrap-Token": bootstrapToken } : {};
  return http.post("/auth/bootstrap-admin", { username, password }, { headers });
}

export async function me() {
  return http.get("/auth/me");
}

export async function logout(refreshToken) {
  return http.post("/auth/logout", { refresh_token: refreshToken });
}
