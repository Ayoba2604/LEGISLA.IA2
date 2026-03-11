from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from time import sleep

import requests

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.config.settings import settings


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a smoke check against the Dockerized backend.")
    parser.add_argument("--base-url", default=settings.docker_smoke_base_url, help="Backend base URL.")
    parser.add_argument("--admin-token", default=settings.admin_token, help="Admin token for /admin endpoints.")
    parser.add_argument("--wait-seconds", type=float, default=0.0, help="Optional wait before checks.")
    args = parser.parse_args()

    if args.wait_seconds > 0:
        sleep(args.wait_seconds)

    session = requests.Session()
    report = {
        "health": fetch_json(session, f"{args.base_url}/health"),
        "health_api": fetch_json(session, f"{args.base_url}{settings.api_prefix}/health"),
        "admin_overview": fetch_json(
            session,
            f"{args.base_url}{settings.api_prefix}/admin/overview",
            headers={"X-Admin-Token": args.admin_token},
        ),
        "chat_probe": fetch_json(
            session,
            f"{args.base_url}/api/v1/chat/query",
            method="POST",
            json_payload={"question": "O que diz o art. 6 do CDC?", "mode": "technical"},
        ),
    }

    failures = [
        name
        for name, payload in report.items()
        if not payload.get("_ok")
    ]
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if failures:
        raise SystemExit(f"Smoke falhou nas etapas: {', '.join(failures)}")


def fetch_json(session: requests.Session, url: str, *, method: str = "GET", headers: dict | None = None, json_payload: dict | None = None) -> dict:
    try:
        response = session.request(method, url, headers=headers, json=json_payload, timeout=20)
        payload = response.json()
        return {"_ok": response.ok, "status_code": response.status_code, "payload": payload}
    except Exception as exc:
        return {"_ok": False, "error": str(exc), "url": url}


if __name__ == "__main__":
    main()
