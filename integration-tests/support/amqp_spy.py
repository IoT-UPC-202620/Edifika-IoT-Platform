"""AMQP Spy to observe events on the edifika.events topic exchange."""

from datetime import datetime
import json
import logging
import threading
import time
from typing import Any
import pika

logger = logging.getLogger(__name__)


class AmqpEventBusSpy:
    """Session-level AMQP listener buffering events published to edifika.events."""

    def __init__(
        self,
        amqp_url: str = "amqp://edifika:edifika-dev@localhost:5672/",
        exchange: str = "edifika.events",
    ):
        self.amqp_url = amqp_url
        self.exchange = exchange
        self._messages: list[tuple[str, dict[str, Any]]] = []
        self._cond = threading.Condition()
        self._stop_event = threading.Event()
        self._connected = threading.Event()
        self._thread: threading.Thread | None = None
        self._connection: pika.BlockingConnection | None = None

    def start(self, timeout: float = 10.0) -> None:
        """Start the background consumer thread."""
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        if not self._connected.wait(timeout):
            raise TimeoutError(f"Failed to connect AMQP spy within {timeout}s")

    def stop(self) -> None:
        """Stop the background consumer."""
        self._stop_event.set()
        if self._connection and self._connection.is_open:
            try:
                self._connection.add_callback_threadsafe(self._connection.close)
            except Exception:
                pass
        if self._thread:
            self._thread.join(timeout=3.0)

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                params = pika.URLParameters(self.amqp_url)
                self._connection = pika.BlockingConnection(params)
                channel = self._connection.channel()
                channel.exchange_declare(exchange=self.exchange, exchange_type="topic", durable=True)
                queue_result = channel.queue_declare(queue="", exclusive=True, auto_delete=True)
                queue_name = queue_result.method.queue
                channel.queue_bind(exchange=self.exchange, queue=queue_name, routing_key="#")

                self._connected.set()
                logger.info("AMQP spy subscribed to exchange %s on queue %s", self.exchange, queue_name)

                for method, properties, body in channel.consume(queue=queue_name, auto_ack=True, inactivity_timeout=1.0):
                    if self._stop_event.is_set():
                        break
                    if method is None:
                        continue
                    try:
                        parsed = json.loads(body.decode("utf-8"))
                        routing_key = method.routing_key
                        logger.debug("AMQP spy received [%s]: %s", routing_key, parsed)
                        with self._cond:
                            self._messages.append((routing_key, parsed))
                            self._cond.notify_all()
                    except Exception as exc:
                        logger.warning("AMQP spy failed to parse message: %s", exc)

                if self._connection.is_open:
                    self._connection.close()
            except Exception as exc:
                if not self._stop_event.is_set():
                    logger.warning("AMQP spy connection error: %s. Reconnecting in 1s...", exc)
                    time.sleep(1.0)

    def get(self, routing_key: str, timeout: float = 10.0) -> dict[str, Any]:
        """Fetch the next message matching routing_key FIFO."""
        deadline = time.monotonic() + timeout
        with self._cond:
            while True:
                for i, (key, msg) in enumerate(self._messages):
                    if self._matches(key, routing_key):
                        self._messages.pop(i)
                        return msg
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    available = [k for k, _ in self._messages]
                    raise TimeoutError(
                        f"No message with routing key '{routing_key}' arrived within {timeout}s. "
                        f"Buffered messages: {available}"
                    )
                self._cond.wait(remaining)

    @staticmethod
    def _matches(actual: str, pattern: str) -> bool:
        if pattern == "#" or actual == pattern:
            return True
        actual_parts = actual.split(".")
        pattern_parts = pattern.split(".")
        # Standard AMQP topic matching (simple cases: exact or single *)
        if len(actual_parts) != len(pattern_parts):
            return False
        return all(p in ("*", a) for a, p in zip(actual_parts, pattern_parts))


class Spy:
    """Handle for checking messages on a specific routing key."""

    def __init__(self, bus_spy: AmqpEventBusSpy, routing_key: str):
        self._bus_spy = bus_spy
        self.routing_key = routing_key

    def get(self, timeout: float = 10.0) -> dict[str, Any]:
        return self._bus_spy.get(self.routing_key, timeout=timeout)
