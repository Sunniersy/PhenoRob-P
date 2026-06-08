import http from "./client";

/**
 * Dashboard API
 *
 * Endpoint for the operations overview dashboard.
 */

export async function overview() {
  return http.get("/dashboard/overview");
}
