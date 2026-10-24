import json
import pathlib
import re

COL = pathlib.Path(__file__).resolve().parents[1] / "postman/Edifika-IoT.postman_collection.json"
CONTRACT_ENDPOINTS = {  # method + path template from contracts §4.2 and §5 (with {id} placeholders normalized to :id)
    ("POST", "/iot/gateways"),
    ("GET", "/iot/gateways"),
    ("GET", "/iot/gateways/:id"),
    ("POST", "/iot/gateways/:id/api-key"),
    ("POST", "/iot/devices"),
    ("GET", "/iot/devices"),
    ("GET", "/iot/devices/:id"),
    ("PATCH", "/iot/devices/:id"),
    ("PUT", "/iot/devices/:id/maintenance"),
    ("DELETE", "/iot/devices/:id"),
    ("GET", "/iot/devices/:id/reservations"),
    ("POST", "/iot/devices/:id/reservations"),
    ("GET", "/access/me/reservations"),
    ("GET", "/access/reservations"),
    ("GET", "/access/reservations/:id"),
    ("DELETE", "/access/reservations/:id"),
    ("POST", "/access/reservations/:id/authorizations"),
    ("GET", "/access/reservations/:id/authorizations"),
    ("DELETE", "/access/reservations/:id/authorizations/:id"),
    ("PUT", "/iot/devices/:id/led"),
    ("GET", "/iot/device-commands/:id"),
    ("POST", "/access/credentials"),
    ("GET", "/access/credentials"),
    ("PATCH", "/access/credentials/:id/status"),
    ("GET", "/access/me/credentials"),
    ("GET", "/access/attempts"),
    ("GET", "/access/me/attempts"),
    ("GET", "/access/me/doors"),
    ("GET", "/access/residents/:id/status"),
    ("POST", "/access/residents/:id/debt-check"),
    ("GET", "/telemetry/devices"),
    ("GET", "/telemetry/devices/:id/latest"),
    ("GET", "/telemetry/readings"),
    ("GET", "/telemetry/alerts"),
    ("GET", "/edge/sync"),
    ("POST", "/authentication/sign-in"),
}


def requests(items):
    for it in items:
        yield from requests(it["item"]) if "item" in it else [it["request"]]


def normalize(raw):  # "{{baseUrl}}/iot/devices/{{deviceId}}?x=1" -> "/iot/devices/:id"
    path = raw.split("{{baseUrl}}", 1)[1].split("?")[0]
    return re.sub(r"\{\{[^}]+\}\}", ":id", path)


def test_collection_covers_every_contract_endpoint():
    col = json.loads(COL.read_text(encoding="utf-8"))
    found = {
        (
            r["method"],
            normalize(r["url"]["raw"] if isinstance(r["url"], dict) else r["url"]),
        )
        for r in requests(col["item"])
    }
    assert CONTRACT_ENDPOINTS <= found


def test_no_secrets_in_collection():
    text = COL.read_text(encoding="utf-8")
    assert "eyJ" not in text and "egk_" not in text
