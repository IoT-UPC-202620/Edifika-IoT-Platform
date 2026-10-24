"""Pytest session configuration and World fixture for H4 e2e tests."""

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
import logging
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Callable
import pytest
import requests

# Ensure integration-tests directory is on pythonpath for support imports
sys.path.insert(0, str(Path(__file__).parent))

from support import tokens
from support.api import Client
from support.mqtt_node import Node
from support.amqp_spy import AmqpEventBusSpy, Spy
from support.wiremock import WireMockClient

logger = logging.getLogger(__name__)

API_GATEWAY_URL = os.environ.get("API_GATEWAY_URL", "http://localhost:8080/api/v1")
EDGE_GATEWAY_URL = os.environ.get("EDGE_GATEWAY_URL", "http://localhost:8000")
WIREMOCK_URL = os.environ.get("WIREMOCK_URL", "http://localhost:8099")
SERVICE_TOKEN = os.environ.get("SERVICE_TOKEN", "dev-service-token")


def window(start_in: int = 70, minutes: int = 3) -> dict[str, str]:
    """Build a startsAt/endsAt window relative to now."""
    now = datetime.now(timezone.utc)
    start = now + timedelta(seconds=start_in)
    end = start + timedelta(minutes=minutes)
    return {
        "startsAt": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "endsAt": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def seconds_until(target_iso: str) -> float:
    """Return seconds remaining until the target ISO-8601 UTC timestamp."""
    target = datetime.fromisoformat(target_iso.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    return max(0.0, (target - now).total_seconds())


def wait_until(predicate: Callable[[], Any], timeout: float = 10.0, interval: float = 0.25) -> Any:
    """Poll predicate until truthy or timeout."""
    deadline = time.monotonic() + timeout
    last_exc = None
    while time.monotonic() < deadline:
        try:
            val = predicate()
            if val:
                return val
        except Exception as exc:
            last_exc = exc
        time.sleep(interval)
    if last_exc:
        raise TimeoutError(f"wait_until failed after {timeout}s: {last_exc}")
    raise TimeoutError(f"wait_until condition was not met within {timeout}s")


class World:
    """End-to-end integration context providing access to all platform interfaces."""

    def __init__(
        self,
        node: Node,
        admin: Client,
        door_id: int,
        wiremock: WireMockClient,
        bus_spy: AmqpEventBusSpy,
    ):
        self.node = node
        self.admin = admin
        self.door_id = door_id
        self.wiremock = wiremock
        self.bus_spy = bus_spy
        self.reservation: dict[str, Any] = {}

    def as_user(self, user_id: int) -> Client:
        return Client(API_GATEWAY_URL, tokens.user(user_id, admin=False))

    def spy(self, routing_key: str) -> Spy:
        return Spy(self.bus_spy, routing_key)

    def wait_sync(self, timeout: float = 10.0) -> None:
        """Wait for the edge gateway to finish a sync cycle."""
        initial_version = None
        try:
            r = requests.get(
                f"{EDGE_GATEWAY_URL}/api/v1/status",
                headers={"Authorization": f"Bearer {SERVICE_TOKEN}"},
                timeout=3,
            )
            if r.status_code == 200:
                initial_version = r.json().get("cache", {}).get("version")
        except Exception:
            pass

        time.sleep(2.0)  # Allow AMQP sync-requested to be delivered and processed
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                r = requests.get(
                    f"{EDGE_GATEWAY_URL}/api/v1/status",
                    headers={"Authorization": f"Bearer {SERVICE_TOKEN}"},
                    timeout=3,
                )
                if r.status_code == 200:
                    v = r.json().get("cache", {}).get("version")
                    if v is not None and (initial_version is None or v != initial_version):
                        return
            except Exception:
                pass
            time.sleep(0.5)

    def compose(self, cmd: str, *services: str) -> None:
        """Run a docker compose command on the e2e stack."""
        args = ["docker", "compose", "-f", "docker-compose.e2e.yml", cmd, *services]
        subprocess.run(args, check=True)


@pytest.fixture(scope="session")
def world() -> World:
    """Setup the live e2e stack, register gateway, door and credentials, and yield World."""
    wiremock = WireMockClient(WIREMOCK_URL)
    wiremock.reset()

    # Ensure access container is running with latest build
    subprocess.run(
        ["docker", "compose", "-f", "docker-compose.e2e.yml", "up", "-d", "access"],
        check=True,
    )
    wait_until(
        lambda: requests.get("http://localhost:8089/v3/api-docs", timeout=2).status_code == 200,
        timeout=30.0,
        interval=1.0,
    )

    bus_spy = AmqpEventBusSpy()
    bus_spy.start(timeout=10.0)

    admin = Client(API_GATEWAY_URL, tokens.user(1, admin=True))

    # 1. Register or find Edge Gateway
    gateways_resp = admin.get("/iot/gateways")
    gateways = gateways_resp.json() if gateways_resp.status_code == 200 else []
    gateway_id = None
    api_key = None

    for gw in gateways:
        if gw.get("gatewayCode") == "edge-gateway-01":
            gateway_id = gw["id"]
            break

    if gateway_id is None:
        create_gw_resp = admin.post(
            "/iot/gateways",
            json={"gatewayCode": "edge-gateway-01", "buildingId": 12, "name": "Torre A"},
        )
        assert create_gw_resp.status_code in (200, 201), f"Failed to create gateway: {create_gw_resp.text}"
        gw_data = create_gw_resp.json()
        gateway_id = gw_data["id"] if "id" in gw_data else gw_data["gatewayId"]
        api_key = gw_data.get("apiKey")
    else:
        # Rotate API key to have clear key
        rotate_resp = admin.post(f"/iot/gateways/{gateway_id}/api-key")
        assert rotate_resp.status_code in (200, 201), f"Failed to rotate apiKey: {rotate_resp.text}"
        api_key = rotate_resp.json().get("apiKey")

    assert api_key, "Could not acquire gateway API key"

    # 2. Launch edge-gateway container with acquired API key
    env = os.environ.copy()
    env["E2E_GATEWAY_API_KEY"] = api_key
    subprocess.run(
        ["docker", "compose", "-f", "docker-compose.e2e.yml", "up", "-d", "edge-gateway"],
        env=env,
        check=True,
    )

    # Wait for edge-gateway health
    wait_until(
        lambda: requests.get(f"{EDGE_GATEWAY_URL}/health", timeout=2).status_code == 200,
        timeout=30.0,
        interval=1.0,
    )

    # 3. Register or find door device
    devices_resp = admin.get("/iot/devices")
    devices = devices_resp.json() if devices_resp.status_code == 200 else []
    door_id = None
    for d in devices:
        if d.get("deviceCode") == "esp32-acc-01":
            door_id = d["id"]
            break

    if door_id is None:
        create_dev_resp = admin.post(
            "/iot/devices",
            json={
                "deviceCode": "esp32-acc-01",
                "gatewayId": gateway_id,
                "name": "Puerta piscina",
                "location": "Piso 1",
                "deviceType": "DOOR",
                "capabilities": [
                    "RFID",
                    "LOCK",
                    "BUZZER",
                    "OLED",
                    "RGB_LED",
                    "TEMPERATURE",
                    "HUMIDITY",
                ],
                "unlockSeconds": 5,
            },
        )
        assert create_dev_resp.status_code in (200, 201), f"Failed to create device: {create_dev_resp.text}"
        door_id = create_dev_resp.json()["id"]

    # 4. Register credentials
    cards = [
        {"uid": "04A1B2C3", "userId": 15, "name": "Ana Perez"},
        {"uid": "04A1B2C4", "userId": 16, "name": "Carlos Perez"},
        {"uid": "04A1B2C5", "userId": 17, "name": "Beatriz Gomez"},
        {"uid": "04A1B2C6", "userId": 18, "name": "David Mora"},
    ]

    creds_resp = admin.get("/access/credentials")
    existing_creds = {c["rfidUid"]: c for c in (creds_resp.json() if creds_resp.status_code == 200 else [])}

    for card in cards:
        uid = card["uid"]
        if uid not in existing_creds:
            admin.post(
                "/access/credentials",
                json={
                    "rfidUid": uid,
                    "buildingId": 12,
                    "userId": card["userId"],
                    "holderName": card["name"],
                    "validFrom": None,
                    "validUntil": None,
                },
            )
        else:
            cid = existing_creds[uid]["id"]
            if existing_creds[uid].get("status") != "ACTIVE":
                admin.patch(f"/access/credentials/{cid}/status", json={"status": "ACTIVE"})

    # Cancel any active or scheduled reservations from previous test runs
    resv_list_resp = admin.get(f"/access/reservations?deviceId={door_id}")
    if resv_list_resp.status_code == 200:
        for r in resv_list_resp.json():
            if r.get("status") in ("SCHEDULED", "ACTIVE"):
                admin.delete(f"/access/reservations/{r['id']}")

    # Refresh debt status for resident 18 while WireMock is clean
    admin.post("/access/residents/18/debt-check")

    # 5. Wait for first cache sync on edge gateway
    wait_until(
        lambda: requests.get(
            f"{EDGE_GATEWAY_URL}/api/v1/status",
            headers={"Authorization": f"Bearer {SERVICE_TOKEN}"},
            timeout=2,
        ).json().get("cache", {}).get("version") is not None,
        timeout=20.0,
        interval=1.0,
    )

    # 6. Start virtual node & send heartbeat to mark device ACTIVE
    node = Node("esp32-acc-01", host="localhost", port=1883)
    node.connect(timeout=10.0)

    def mark_active():
        node.publish_heartbeat()
        resp = admin.get(f"/iot/devices/{door_id}")
        return resp.status_code == 200 and resp.json().get("status") == "ACTIVE"

    wait_until(
        mark_active,
        timeout=25.0,
        interval=1.0,
    )

    # Clear setup commands (e.g. the initial mode: FREE_ACCESS sent during touch)
    node._commands.clear()

    w = World(node, admin, door_id, wiremock, bus_spy)

    try:
        yield w
    finally:
        node.disconnect()
        bus_spy.stop()
