import { getAuthToken } from "../api/client";

let socket;
let reconnectTimer;
let reconnectAttempts = 0;
let manualClose = false;
let pingTimer = null;

const PING_INTERVAL = 30000;
const MAX_RECONNECT_ATTEMPTS = 50;
const EVENT_ID_KEY = "phenobot-last-event-id";

function nextReconnectDelay() {
  if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
    console.warn(`ws reconnect limit reached (${MAX_RECONNECT_ATTEMPTS}), giving up`);
    return null;
  }
  const delay = Math.min(5000, 800 * 2 ** reconnectAttempts);
  reconnectAttempts += 1;
  return delay;
}

function startPing(ws) {
  stopPing();
  pingTimer = setInterval(() => {
    if (ws.readyState === WebSocket.OPEN) {
      try { ws.send(JSON.stringify({ type: "ping" })); } catch { /* ignore */ }
    }
  }, PING_INTERVAL);
}

function stopPing() {
  if (pingTimer) {
    clearInterval(pingTimer);
    pingTimer = null;
  }
}

export function connectEventSocket({ onMessage, onOpen, onClose, onError } = {}) {
  const token = getAuthToken();
  if (!token) return null;
  const lastEventId = localStorage.getItem(EVENT_ID_KEY) || "0";
  if (socket) {
    manualClose = true;
    socket.close();
  }
  manualClose = false;
  const protocol = location.protocol === "https:" ? "wss" : "ws";
  // Token is sent as the first WebSocket message instead of a URL query parameter
  // to prevent it from being recorded in server access logs, browser history, and
  // proxy/CDN logs.
  const nextSocket = new WebSocket(
    `${protocol}://${location.host}/ws/events`
  );
  socket = nextSocket;
  let authenticated = false;
  nextSocket.onopen = () => {
    reconnectAttempts = 0;
    // Send authentication as the first message immediately after connection opens.
    nextSocket.send(JSON.stringify({
      type: "auth",
      token,
      last_event_id: Number(lastEventId) || 0,
    }));
  };
  nextSocket.onmessage = (event) => {
    try {
      const payload = JSON.parse(event.data);

      // Handle server auth response before the connection is considered ready.
      if (payload?.type === "auth_ok") {
        authenticated = true;
        startPing(nextSocket);
        onOpen?.();
        return;
      }
      if (payload?.type === "auth_error") {
        console.error("ws auth failed:", payload.message);
        nextSocket.close();
        return;
      }

      // Discard any event messages received before authentication completes.
      if (!authenticated) return;

      if (!payload?.event) return;
      if (payload?.id) {
        localStorage.setItem(EVENT_ID_KEY, String(payload.id));
      }
      onMessage?.(payload);
    } catch (error) {
      console.error("ws message parse failed", error);
    }
  };
  nextSocket.onerror = (event) => onError?.(event);
  nextSocket.onclose = () => {
    stopPing();
    if (socket === nextSocket) {
      socket = null;
    }
    onClose?.();
    if (manualClose) return;
    clearTimeout(reconnectTimer);
    const delay = nextReconnectDelay();
    if (delay === null) return;
    reconnectTimer = setTimeout(() => {
      if (!getAuthToken()) return;
      connectEventSocket({ onMessage, onOpen, onClose, onError });
    }, delay);
  };
  return nextSocket;
}

export function closeEventSocket() {
  clearTimeout(reconnectTimer);
  stopPing();
  if (socket) {
    manualClose = true;
    socket.close();
    socket = null;
  }
}
