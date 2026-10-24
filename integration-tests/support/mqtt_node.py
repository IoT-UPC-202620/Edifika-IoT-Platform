"""Virtual ESP32 MQTT Node matching the reference firmware dialect (v1)."""

from datetime import datetime, timezone
import json
import logging
import os
import threading
import time
from typing import Any
import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class Node:
    """Simulates an ESP32 node speaking the reference v1 firmware dialect."""

    def __init__(
        self,
        device_code: str,
        host: str = "localhost",
        port: int = 1883,
        prefix: str = "edifika/v1",
    ):
        self.device_code = device_code
        self.host = host
        self.port = port
        self.prefix = prefix
        self.heartbeat_interval = 8.0
        self._commands: list[dict[str, Any]] = []
        self._cond = threading.Condition()
        self._connected = threading.Event()
        self._stop_heartbeat = threading.Event()
        self._heartbeat_thread: threading.Thread | None = None

        client_id = f"test-node-{device_code}-{os.getpid()}-{int(time.time()*1000)%10000}"
        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=client_id,
        )
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    def _topic(self, channel: str) -> str:
        return f"{self.prefix}/nodes/{self.device_code}/{channel}"

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        logger.debug("Node %s connected to MQTT broker", self.device_code)
        sub_topic = self._topic("commands")
        client.subscribe(sub_topic, qos=1)
        self._connected.set()

    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            logger.debug("Node %s received command: %s", self.device_code, payload)
            with self._cond:
                self._commands.append(payload)
                self._cond.notify_all()
        except Exception as exc:
            logger.warning("Node %s failed to parse MQTT message: %s", self.device_code, exc)

    def _heartbeat_loop(self) -> None:
        while not self._stop_heartbeat.wait(self.heartbeat_interval):
            try:
                self.publish_heartbeat()
            except Exception as exc:
                logger.debug("Node %s periodic heartbeat error: %s", self.device_code, exc)

    def connect(self, timeout: float = 5.0) -> None:
        """Connect to broker and start the background network loop."""
        self.client.connect(self.host, self.port, keepalive=30)
        self.client.loop_start()
        if not self._connected.wait(timeout):
            raise TimeoutError(f"Failed to connect to MQTT broker {self.host}:{self.port} within {timeout}s")
        if self.heartbeat_interval > 0:
            self._stop_heartbeat.clear()
            self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
            self._heartbeat_thread.start()

    def disconnect(self) -> None:
        """Stop background loop and disconnect from broker."""
        self._stop_heartbeat.set()
        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            self._heartbeat_thread.join(timeout=1.0)
        self.client.loop_stop()
        self.client.disconnect()

    def publish_heartbeat(self, fw: str = "v0.3.0") -> None:
        """Publish a heartbeat message containing deviceId."""
        payload = {
            "v": "1",
            "ts": _now_iso(),
            "deviceId": self.device_code,
            "fw": fw,
        }
        self.client.publish(self._topic("heartbeat"), json.dumps(payload), qos=1)

    def tap(self, uid: str, timeout: float = 3.0) -> dict[str, Any]:
        """Present an RFID card and wait for the access_result command."""
        with self._cond:
            self._commands = [c for c in self._commands if c.get("type") != "access_result"]
        payload = {
            "v": "1",
            "ts": _now_iso(),
            "credentialType": "RFID",
            "credential": uid,
        }
        self.client.publish(self._topic("access"), json.dumps(payload), qos=1)
        return self.wait_command("access_result", timeout=timeout)

    def clear_commands(self) -> None:
        """Clear buffered commands."""
        with self._cond:
            self._commands.clear()

    def wait_command(self, type_: str, timeout: float = 5.0, predicate: Any = None) -> dict[str, Any]:
        """Wait for the next command matching the specified type."""
        deadline = time.monotonic() + timeout
        with self._cond:
            while True:
                for i, cmd in enumerate(self._commands):
                    if cmd.get("type") == type_:
                        if predicate is None or predicate(cmd):
                            return self._commands.pop(i)
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError(
                        f"Command '{type_}' not received by {self.device_code} within {timeout}s. "
                        f"Current commands: {self._commands}"
                    )
                self._cond.wait(remaining)

    def ack(self, command_id: str, status: str = "OK", detail: str = "") -> None:
        """Acknowledge a command execution."""
        payload = {
            "v": "1",
            "ts": _now_iso(),
            "commandId": command_id,
            "status": status,
            "detail": detail,
        }
        self.client.publish(self._topic("ack"), json.dumps(payload), qos=1)

    def publish_reading(self, sensor: str, value: float | int | None, unit: str) -> None:
        """Publish a sensor reading."""
        payload = {
            "v": "1",
            "ts": _now_iso(),
            "sensor": sensor,
            "value": value,
            "unit": unit,
        }
        self.client.publish(self._topic("readings"), json.dumps(payload), qos=1)
