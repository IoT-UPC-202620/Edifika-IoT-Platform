"""Smoke test to verify that the World fixture brings up all interfaces."""

def test_world_is_ready(world):
    resp = world.admin.get(f"/iot/devices/{world.door_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ACTIVE"
    assert data["deviceCode"] == "esp32-acc-01"
