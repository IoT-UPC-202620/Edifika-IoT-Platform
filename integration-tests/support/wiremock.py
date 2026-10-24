"""WireMock helper client for dynamic debt and residential stubs."""

import requests


class WireMockClient:
    """Controls WireMock stubs via its __admin API."""

    def __init__(self, base_url: str = "http://localhost:8099"):
        self.base_url = base_url.rstrip("/")

    def set_debts(self, unit_id: int, debts: list[dict]) -> None:
        """Stub debts for a specific unit with high priority."""
        mapping = {
            "priority": 1,
            "request": {
                "method": "GET",
                "urlPath": f"/api/v1/payments/debts/unit/{unit_id}",
            },
            "response": {
                "status": 200,
                "headers": {
                    "Content-Type": "application/json",
                },
                "jsonBody": debts,
            },
        }
        resp = requests.post(f"{self.base_url}/__admin/mappings", json=mapping, timeout=5)
        resp.raise_for_status()

    def reset(self) -> None:
        """Reset WireMock mappings back to defaults loaded from files."""
        resp = requests.post(f"{self.base_url}/__admin/mappings/reset", timeout=5)
        resp.raise_for_status()
