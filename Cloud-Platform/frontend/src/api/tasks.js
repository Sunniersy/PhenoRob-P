import http from "./client";

/**
 * Tasks API
 *
 * Endpoints for task lifecycle management: listing, creation,
 * dispatching, retrying, and cancellation.
 */

export async function list(params) {
  return http.get("/tasks", { params });
}

export async function get(id) {
  return http.get(`/tasks/${id}`);
}

export async function create(data) {
  return http.post("/tasks", data);
}

export async function dispatch(id) {
  return http.post(`/tasks/${id}/dispatch`);
}

export async function retry(id) {
  return http.post(`/tasks/${id}/retry`);
}

export async function cancel(id) {
  return http.post(`/tasks/${id}/cancel`);
}
