"""HTTP Client wrapper for integration tests through ApiGateway."""

from typing import Any
import requests


class Client:
    """REST API Client with bearer token and base URL management."""

    def __init__(self, base_url: str, token: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.session = requests.Session()

    def _url(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        if not path.startswith("/"):
            path = "/" + path
        return f"{self.base_url}{path}"

    def _headers(self, headers: dict[str, str] | None = None) -> dict[str, str]:
        h: dict[str, str] = {"Content-Type": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        if headers:
            h.update(headers)
        return h

    def get(self, path: str, **kwargs: Any) -> requests.Response:
        kwargs["headers"] = self._headers(kwargs.get("headers"))
        return self.session.get(self._url(path), **kwargs)

    def post(self, path: str, **kwargs: Any) -> requests.Response:
        kwargs["headers"] = self._headers(kwargs.get("headers"))
        return self.session.post(self._url(path), **kwargs)

    def put(self, path: str, **kwargs: Any) -> requests.Response:
        kwargs["headers"] = self._headers(kwargs.get("headers"))
        return self.session.put(self._url(path), **kwargs)

    def patch(self, path: str, **kwargs: Any) -> requests.Response:
        kwargs["headers"] = self._headers(kwargs.get("headers"))
        return self.session.patch(self._url(path), **kwargs)

    def delete(self, path: str, **kwargs: Any) -> requests.Response:
        kwargs["headers"] = self._headers(kwargs.get("headers"))
        return self.session.delete(self._url(path), **kwargs)
