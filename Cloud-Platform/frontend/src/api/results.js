import http, { authFetchBlob } from "./client";

/**
 * Results API
 *
 * Endpoints for listing analysis results and downloading result files.
 */

export async function list(params) {
  return http.get("/results", { params });
}

export async function download(taskId) {
  return authFetchBlob(`/api/results/${taskId}/download?download=1`);
}
