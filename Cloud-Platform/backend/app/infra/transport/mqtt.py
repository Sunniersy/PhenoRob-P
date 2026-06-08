import json
import logging
import os
import time
from threading import Event
from uuid import uuid4

logger = logging.getLogger(__name__)

from shared.mqtt import TopicFactory

from .base import RobotTransport


class MqttTransport(RobotTransport):
    def __init__(self, config: dict):
        import paho.mqtt.client as mqtt

        self.config = config
        self._connected = Event()
        self.client_id = self.build_client_id(config["MQTT_CLIENT_ID"])
        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=self.client_id,
        )
        if config["MQTT_USERNAME"]:
            self.client.username_pw_set(config["MQTT_USERNAME"], config["MQTT_PASSWORD"])
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.client.connect(config["MQTT_BROKER_HOST"], config["MQTT_BROKER_PORT"])
        self.client.loop_start()
        if not self._connected.wait(timeout=10):
            raise TimeoutError("mqtt broker connection timed out")

    def _subscribe_topics(self):
        self.client.subscribe(f"{TopicFactory.PREFIX}/robots/+/heartbeat", qos=self.config["MQTT_QOS"])
        self.client.subscribe(f"{TopicFactory.PREFIX}/robots/+/status", qos=self.config["MQTT_QOS"])
        self.client.subscribe(f"{TopicFactory.PREFIX}/robots/+/progress", qos=self.config["MQTT_QOS"])
        self.client.subscribe(f"{TopicFactory.PREFIX}/robots/+/ack", qos=self.config["MQTT_QOS"])
        self.client.subscribe(f"{TopicFactory.PREFIX}/robots/+/events", qos=self.config["MQTT_QOS"])
        self.client.subscribe(f"{TopicFactory.PREFIX}/robots/+/command-events", qos=self.config["MQTT_QOS"])

    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        self._connected.set()
        self._subscribe_topics()

    def _on_disconnect(self, client, userdata, *args, **kwargs):
        self._connected.clear()

    def _ensure_connected(self, max_retries: int = 5) -> None:
        if self._connected.is_set():
            return

        for attempt in range(max_retries):
            try:
                self.client.reconnect()
                if self._connected.wait(timeout=5):
                    return
            except Exception as exc:
                logger.warning("mqtt reconnect attempt %d/%d failed: %s", attempt + 1, max_retries, exc)
            if attempt < max_retries - 1:
                backoff = min(2 ** attempt, 16)
                time.sleep(backoff)

        raise RuntimeError("mqtt broker is not connected after %d retries" % max_retries)

    def _on_message(self, client, userdata, message):
        parts = message.topic.split("/")
        if len(parts) < 4:
            self.task_service.handle_protocol_error(
                "unknown",
                {
                    "topic": message.topic,
                    "error": "invalid topic structure",
                    "source": "mqtt_transport",
                },
            )
            return
        robot_code = parts[2]
        channel = parts[3]
        try:
            payload = json.loads(message.payload.decode("utf-8"))
        except json.JSONDecodeError as exc:
            self.task_service.handle_protocol_error(
                robot_code,
                {
                    "topic": message.topic,
                    "error": f"invalid json payload: {exc}",
                    "source": "mqtt_transport",
                },
            )
            return
        if channel == "heartbeat":
            self.robot_service.handle_heartbeat(robot_code, payload)
        elif channel == "status":
            self.robot_service.handle_status(robot_code, payload)
        elif channel == "progress":
            self.task_service.handle_progress(robot_code, payload)
        elif channel == "ack":
            self.task_service.handle_ack(robot_code, payload)
        elif channel == "events":
            self.task_service.handle_exception_event(robot_code, payload)
        elif channel == "command-events":
            self.robot_service.handle_command_event(robot_code, payload)
        else:
            self.task_service.handle_protocol_error(
                robot_code,
                {
                    "topic": message.topic,
                    "error": f"unknown channel {channel}",
                    "payload": payload,
                    "source": "mqtt_transport",
                },
            )

    def publish_task(self, robot_code: str, payload: dict) -> None:
        self._ensure_connected()
        self.client.publish(
            TopicFactory.task_dispatch(robot_code),
            json.dumps(payload),
            qos=self.config["MQTT_QOS"],
        )

    def publish_command(self, robot_code: str, payload: dict) -> None:
        self._ensure_connected()
        self.client.publish(
            TopicFactory.robot_command(robot_code),
            json.dumps(payload),
            qos=self.config["MQTT_QOS"],
        )

    @staticmethod
    def build_client_id(base_client_id: str, pid: int | None = None, nonce: str | None = None) -> str:
        safe_base = base_client_id or "cloud-server"
        process_id = pid if pid is not None else os.getpid()
        instance_nonce = nonce or uuid4().hex[:8]
        return f"{safe_base}-{process_id}-{instance_nonce}"

    def describe(self) -> dict:
        return {
            "backend": "mqtt",
            "host": self.config["MQTT_BROKER_HOST"],
            "connected": self._connected.is_set(),
            "client_id": self.client_id,
        }

    def healthcheck(self) -> dict:
        if not self._connected.is_set():
            raise RuntimeError("mqtt transport disconnected")
        return self.describe()
