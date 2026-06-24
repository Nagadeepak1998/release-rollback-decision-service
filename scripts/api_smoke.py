from __future__ import annotations

import json

from fastapi.testclient import TestClient

from app.main import app


def main() -> None:
    payload = json.loads(open("samples/risky_release.json", encoding="utf-8").read())
    client = TestClient(app)
    health = client.get("/healthz")
    decision = client.post("/evaluate", json=payload)
    metrics = client.get("/metrics")

    print(f"GET /healthz -> {health.status_code} {health.json()['status']}")
    print(
        "POST /evaluate -> "
        f"{decision.status_code} {decision.json()['decision']} score={decision.json()['score']}"
    )
    print(f"GET /metrics -> {metrics.status_code} metrics_bytes={len(metrics.text)}")


if __name__ == "__main__":
    main()
