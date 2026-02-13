#!/usr/bin/env python3
"""Mini API-Gateway, um Daten an GoHighLevel (LeadConnector) zu senden."""

from __future__ import annotations

import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

API_URL = "https://services.leadconnectorhq.com/contacts/"
API_VERSION = "2021-07-28"


def build_contact_payload(data: dict[str, Any], location_id: str) -> dict[str, Any]:
    return {
        "locationId": location_id,
        "firstName": data.get("firstName", ""),
        "lastName": data.get("lastName", ""),
        "name": data.get("name", ""),
        "email": data.get("email", ""),
        "phone": data.get("phone", ""),
        "source": data.get("source", "api-gateway"),
        "customFields": data.get("customFields", []),
        "tags": data.get("tags", []),
    }


def send_to_ghl(payload: dict[str, Any], api_key: str) -> tuple[int, dict[str, Any]]:
    req = Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Version": API_VERSION,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(req, timeout=15) as response:
            body = response.read().decode("utf-8") or "{}"
            return response.status, json.loads(body)
    except HTTPError as exc:
        body = exc.read().decode("utf-8") or "{}"
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            parsed = {"raw": body}
        return exc.code, {"error": "ghl_http_error", "details": parsed}
    except URLError as exc:
        return 502, {"error": "ghl_connection_error", "details": str(exc)}


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/api/ghl/contact":
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "not_found"})
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(content_length)
        try:
            incoming = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "invalid_json"})
            return

        api_key = os.getenv("GHL_API_KEY", "")
        location_id = os.getenv("GHL_LOCATION_ID", "")

        if not location_id:
            self._send_json(
                HTTPStatus.BAD_REQUEST,
                {
                    "error": "missing_location_id",
                    "hint": "Bitte setze GHL_LOCATION_ID als Umgebungsvariable.",
                },
            )
            return

        payload = build_contact_payload(incoming, location_id)

        if not api_key:
            self._send_json(
                HTTPStatus.OK,
                {
                    "mode": "dry-run",
                    "message": "Kein GHL_API_KEY gesetzt. Anfrage wurde nur lokal validiert.",
                    "would_send": payload,
                },
            )
            return

        status, response_body = send_to_ghl(payload, api_key)
        self._send_json(status, {"mode": "live", "ghl": response_body})


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"GHL Gateway läuft auf http://0.0.0.0:{port}")
    server.serve_forever()
