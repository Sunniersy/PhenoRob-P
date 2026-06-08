import http from "./client";

/**
 * Admin API
 *
 * Endpoints for user management, role listing, and alert management.
 */

export async function listUsers(params) {
  return http.get("/users", { params });
}

export async function createUser(data) {
  return http.post("/users", data);
}

export async function toggleUserStatus(userId, isActive) {
  return http.patch(`/users/${userId}/status`, { is_active: isActive });
}

export async function resetPassword(userId, password) {
  return http.post(`/users/${userId}/reset-password`, { password });
}

export async function listRoles(params) {
  return http.get("/roles", { params });
}

export async function listAlerts(params) {
  return http.get("/system/alerts", { params });
}

export async function acknowledgeAlert(alertId, isAcknowledged) {
  return http.patch(`/system/alerts/${alertId}/status`, {
    is_acknowledged: isAcknowledged
  });
}
