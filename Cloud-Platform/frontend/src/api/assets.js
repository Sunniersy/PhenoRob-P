import http from "./client";

/**
 * Assets API
 *
 * Endpoints for listing/getting assets and managing the
 * multi-step upload workflow (create session, upload content, complete).
 */

export async function list(params) {
  return http.get("/assets", { params });
}

export async function get(id) {
  return http.get(`/assets/${id}`);
}

export async function createUploadSession(data) {
  return http.post("/assets/upload-sessions", data);
}

export async function uploadContent(sessionId, formData, { onUploadProgress } = {}) {
  return http.put(`/assets/upload-sessions/${sessionId}/content`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
    timeout: 0,
    onUploadProgress
  });
}

export async function completeUpload(sessionId, data) {
  return http.post(`/assets/upload-sessions/${sessionId}/complete`, data);
}
