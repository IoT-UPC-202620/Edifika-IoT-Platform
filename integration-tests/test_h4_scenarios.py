"""H4 End-to-End Integration Scenarios (7 business flows)."""

import time
import pytest
from conftest import window, seconds_until, wait_until


def test_1_free_access_resident_up_to_date_enters(world):
    """Scenario 1: Resident up-to-date enters during FREE_ACCESS and domain event is emitted."""
    r = world.node.tap("04A1B2C5")
    assert r["params"]["result"] == "GRANTED"
    event = world.spy("access.physical-access-granted").get(10)
    assert event["payload"]["userId"] == 17


def test_2_delinquent_is_denied_and_cannot_reserve(world):
    """Scenario 2: Delinquent resident is denied access, suspended, and cannot create reservations."""
    world.wiremock.set_debts(
        43,
        [
            {
                "id": 1,
                "unitId": 43,
                "description": "Mantenimiento",
                "amount": 100,
                "currency": "PEN",
                "dueDate": "2026-09-01",
                "status": "OVERDUE",
            }
        ],
    )
    resp_dc = world.admin.post("/access/residents/18/debt-check")
    assert resp_dc.status_code == 200
    world.wait_sync()

    r = world.node.tap("04A1B2C6")
    assert (r["params"]["result"], r["params"]["reason"]) == ("DENIED", "credential_suspended")

    denied_event = world.spy("access.physical-access-denied").get(10)
    assert denied_event["payload"]["reason"] == "DELINQUENT"

    resp = world.as_user(18).post(
        f"/iot/devices/{world.door_id}/reservations",
        json=window(start_in=90, minutes=5),
    )
    assert resp.status_code == 409
    assert resp.json()["message"] == "El residente tiene deudas vencidas"


def test_3_reservation_switches_node_to_reserved(world):
    """Scenario 3: Resident reserves door space; gateway switches door mode to RESERVED."""
    resv_resp = world.as_user(15).post(
        f"/iot/devices/{world.door_id}/reservations",
        json=window(start_in=70, minutes=3),
    )
    assert resv_resp.status_code in (200, 201), f"Reservation failed: {resv_resp.text}"
    resv = resv_resp.json()

    auth_resp = world.as_user(15).post(
        f"/access/reservations/{resv['id']}/authorizations",
        json={"userId": 16},
    )
    assert auth_resp.status_code in (200, 201), f"Authorization failed: {auth_resp.text}"

    cmd = world.node.wait_command(
        "mode",
        timeout=85,
        predicate=lambda c: c.get("params", {}).get("mode") == "RESERVED",
    )
    assert cmd["params"]["mode"] == "RESERVED"

    # Wait until Access Management scheduler transitions device accessMode to RESERVED
    wait_until(
        lambda: world.admin.get(f"/iot/devices/{world.door_id}").json().get("accessMode") == "RESERVED",
        timeout=35.0,
        interval=1.0,
    )
    world.reservation = resv


def test_4_during_reservation_only_holder_and_guest_enter(world):
    """Scenario 4: During reservation, only the holder and authorized guest can enter."""
    r_holder = world.node.tap("04A1B2C3")
    assert r_holder["params"]["result"] == "GRANTED"  # holder 15

    r_guest = world.node.tap("04A1B2C4")
    assert r_guest["params"]["result"] == "GRANTED"  # guest 16

    r_other = world.node.tap("04A1B2C5")
    assert (r_other["params"]["result"], r_other["params"]["reason"]) == ("DENIED", "not_authorized")


def test_5_led_by_holder_reaches_node_and_others_are_rejected(world):
    """Scenario 5: Holder can change LED during RESERVED; non-holders rejected (403)."""
    # Ensure Access service is confirmed in RESERVED mode
    wait_until(
        lambda: world.admin.get(f"/iot/devices/{world.door_id}").json().get("accessMode") == "RESERVED",
        timeout=35.0,
        interval=1.0,
    )
    t0 = time.monotonic()
    led_resp = world.as_user(15).put(
        f"/iot/devices/{world.door_id}/led",
        json={"color": "#00ff88"},
    )
    assert led_resp.status_code == 202
    cmd = led_resp.json()

    node_cmd = world.node.wait_command("rgb", timeout=5)
    world.node.ack(node_cmd["commandId"])
    assert node_cmd["params"] == {"color": "#00FF88"}
    assert node_cmd["commandId"] == cmd["commandId"]

    wait_until(
        lambda: world.as_user(15).get(f"/iot/device-commands/{cmd['commandId']}").json().get("status") == "OK",
        timeout=5.0,
    )
    assert time.monotonic() - t0 < 5.0

    forbidden_resp = world.as_user(17).put(
        f"/iot/devices/{world.door_id}/led",
        json={"color": "#FF0000"},
    )
    assert forbidden_resp.status_code == 403


def test_6_reservation_ends_offline_and_door_returns_to_free_access(world):
    """Scenario 6: Even with cloud offline, local gateway returns door to FREE_ACCESS at reservation end."""
    try:
        world.compose("stop", "rabbitmq", "access")

        remaining = seconds_until(world.reservation["endsAt"])
        cmd = world.node.wait_command(
            "mode",
            timeout=remaining + 15,
            predicate=lambda c: c.get("params", {}).get("mode") == "FREE_ACCESS",
        )
        assert cmd["params"]["mode"] == "FREE_ACCESS"

        r = world.node.tap("04A1B2C5")
        assert r["params"]["result"] == "GRANTED"
    finally:
        world.compose("start", "rabbitmq", "access")

    # Wait for access service to be back online
    wait_until(
        lambda: world.as_user(15).put(f"/iot/devices/{world.door_id}/led", json={"color": "#FF0000"}).status_code == 409,
        timeout=30.0,
        interval=1.0,
    )


def test_7_telemetry_every_10s_visible(world):
    """Scenario 7: Sensor telemetry sent via MQTT is stored and visible on REST API."""
    def check_telemetry():
        world.node.publish_reading("temperature", 24.5, "°C")
        world.node.publish_reading("humidity", 61.0, "%")
        resp = world.admin.get("/telemetry/devices/esp32-acc-01/latest")
        if resp.status_code != 200:
            return False
        latest = resp.json().get("latest", [])
        magnitudes = {item.get("magnitude") for item in latest}
        return {"TEMPERATURE", "HUMIDITY"}.issubset(magnitudes)

    wait_until(check_telemetry, timeout=25.0, interval=2.0)
