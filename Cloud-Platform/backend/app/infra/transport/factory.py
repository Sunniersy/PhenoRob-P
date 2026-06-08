from .in_memory import InMemoryTransport
from .mqtt import MqttTransport


def create_transport(config: dict):
    if config["TRANSPORT_BACKEND"] == "mqtt":
        try:
            return MqttTransport(config)
        except Exception:
            if not config["ALLOW_RUNTIME_FALLBACK"]:
                raise
    return InMemoryTransport()
