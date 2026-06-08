import http from "./client";

/**
 * Downloads API
 *
 * Endpoint for obtaining a one-time download token.
 * Note: authFetchBlob in client.js handles this internally
 * for authenticated blob downloads. This module exposes the
 * raw token exchange for custom use cases.
 */

export async function getToken(path) {
  return http.post("/downloads/token", { path });
}
