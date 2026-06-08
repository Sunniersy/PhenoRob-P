import json
import time
import logging
from datetime import datetime, timezone

from flask import Blueprint, Response, current_app, request

bp = Blueprint("ws", __name__)
logger = logging.getLogger(__name__)

try:
    from flask_sock import Sock
except Exception:  # pragma: no cover - optional runtime dependency
    Sock = None

# Timeout (seconds) for the client to send the initial auth message.
AUTH_TIMEOUT = 10

# Maximum number of concurrent WebSocket connections
MAX_CONNECTIONS = 100

# Ping interval (seconds) to detect dead connections
PING_INTERVAL = 30

# Active connections tracking
active_connections = 0


def register_ws(app):
    app.register_blueprint(bp)
    if not app.config["WEBSOCKET_ENABLED"] or Sock is None:
        return

    sock = Sock(app)

    @sock.route("/ws/events")
    def events(ws):
        global active_connections

        # Check connection limit
        if active_connections >= MAX_CONNECTIONS:
            ws.send(json.dumps({"type": "error", "message": "connection limit reached"}))
            return

        active_connections += 1
        logger.info(f"WebSocket connection opened. Active: {active_connections}")

        try:
            _handle_connection(ws)
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            active_connections -= 1
            logger.info(f"WebSocket connection closed. Active: {active_connections}")


def _handle_connection(ws):
    # ── Step 1: wait for the client's first message carrying auth token ──
    # Token is no longer read from the URL query string to avoid leaking it
    # into server access logs, browser history, and proxy logs.
    raw = ws.receive(timeout=AUTH_TIMEOUT)
    if raw is None:
        return

    try:
        auth_msg = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        ws.send(json.dumps({"type": "auth_error", "message": "invalid JSON"}))
        return

    token = (auth_msg or {}).get("token", "")
    if not token:
        ws.send(json.dumps({"type": "auth_error", "message": "missing token"}))
        return

    try:
        current_app.extensions["auth_service"].current_user(token)
    except Exception:
        ws.send(json.dumps({"type": "auth_error", "message": "authentication failed"}))
        return

    # Acknowledge successful authentication so the client can start its
    # ping timer and begin processing events.
    ws.send(json.dumps({"type": "auth_ok"}))

    # ── Step 2: main event loop (only reached after successful auth) ──
    broker = current_app.extensions["realtime"]
    last_event_id = int((auth_msg or {}).get("last_event_id", 0) or 0)
    last_ping_time = time.time()
    consecutive_empty = 0

    while True:
        try:
            # Check for new events
            items = broker.fetch_after(last_event_id)
            if items:
                consecutive_empty = 0
                for item in items:
                    ws.send(
                        json.dumps(
                            {
                                "id": item["id"],
                                "event": item["event"],
                                "payload": item["payload"],
                                "timestamp": item["timestamp"],
                            },
                            ensure_ascii=False,
                        )
                    )
                    last_event_id = item["id"]
            else:
                consecutive_empty += 1

                # Send ping to detect dead connections
                current_time = time.time()
                if current_time - last_ping_time >= PING_INTERVAL:
                    try:
                        ws.send(json.dumps({"type": "ping"}))
                        last_ping_time = current_time
                    except Exception:
                        logger.debug("Failed to send ping, connection may be dead")
                        break

                # Adaptive sleep: sleep longer when no events
                sleep_time = min(0.5 + (consecutive_empty * 0.1), 2.0)
                message = ws.receive(timeout=sleep_time)

                if message is None:
                    # Timeout, continue loop
                    continue

                # Handle client messages (pong, close, etc.)
                try:
                    msg = json.loads(message)
                    if msg.get("type") == "pong":
                        # Client is alive
                        continue
                    elif msg.get("type") == "close":
                        # Client wants to close
                        break
                except (json.JSONDecodeError, TypeError):
                    # Ignore invalid messages
                    pass

        except Exception as e:
            logger.error(f"WebSocket loop error: {e}")
            # Try to send error to client
            try:
                ws.send(json.dumps({"type": "error", "message": "internal error"}))
            except Exception:
                pass
            break


@bp.get("/ws/events")
def ws_unavailable():
    return Response("WebSocket backend unavailable. Install flask-sock to enable /ws/events.", status=501)
