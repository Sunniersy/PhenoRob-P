import http from "./client";

/**
 * System API
 *
 * Endpoints for health/bootstrap checks and runtime information.
 */

export async function bootstrapCheck() {
  return http.get("/system/bootstrap-check");
}

export async function runtime() {
  return http.get("/system/runtime");
}
