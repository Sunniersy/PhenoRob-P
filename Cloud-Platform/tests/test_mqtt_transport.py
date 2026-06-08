from threading import Event

from backend.app.infra.transport.mqtt import MqttTransport
from shared.mqtt import TopicFactory


def test_publish_task_reconnects_before_sending_when_connection_is_stale():
    published = []
    connected = Event()

    class FakeClient:
        def reconnect(self):
            connected.set()

        def publish(self, topic, payload, qos):
            published.append({"topic": topic, "payload": payload, "qos": qos})

    transport = object.__new__(MqttTransport)
    transport.config = {"MQTT_QOS": 1, "MQTT_BROKER_HOST": "mosquitto", "MQTT_BROKER_PORT": 1883}
    transport.client = FakeClient()
    transport._connected = connected

    transport.publish_task("robot-001", {"task_id": "task-001"})

    assert published == [
        {
            "topic": TopicFactory.task_dispatch("robot-001"),
            "payload": '{"task_id": "task-001"}',
            "qos": 1,
        }
    ]


def test_mqtt_client_id_is_unique_per_process_instance():
    first = MqttTransport.build_client_id("cloud-server-backend", pid=1001, nonce="abc123ef")
    second = MqttTransport.build_client_id("cloud-server-backend", pid=1002, nonce="abc123ef")
    third = MqttTransport.build_client_id("cloud-server-backend", pid=1001, nonce="fed321ab")

    assert first == "cloud-server-backend-1001-abc123ef"
    assert second != first
    assert third != first
