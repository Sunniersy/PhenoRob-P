import http from "./client";

/**
 * Robots API
 *
 * Endpoints for robot registration, listing, command history,
 * and sending commands to devices.
 */

export async function list(params) {
  return http.get("/robots", { params });
}

export async function register(data) {
  return http.post("/robots/register", data);
}

export async function listCommands(robotId, params) {
  return http.get(`/robots/${robotId}/commands`, { params });
}

export async function sendCommand(robotId, command, params = {}) {
  return http.post(`/robots/${robotId}/commands`, { command, params });
}
