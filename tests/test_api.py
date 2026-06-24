from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_healthz() -> None:
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_evaluate_endpoint_matches_shared_engine() -> None:
    payload = {
        "service": "checkout-api",
        "environment": "production",
        "version": "2026.06.24-rc3",
        "deployment_age_minutes": 7,
        "error_rate_percent": 6.4,
        "baseline_error_rate_percent": 0.8,
        "p95_latency_ms": 920,
        "baseline_p95_latency_ms": 410,
        "saturation_percent": 91,
        "failed_synthetic_checks": 4,
        "canary_traffic_percent": 60,
        "customer_impact_count": 32,
        "open_sev1_incident": True,
        "change_freeze_active": False,
    }

    response = client.post("/evaluate", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["decision"] == "rollback"
    assert body["score"] >= 70


def test_metrics_endpoint_exposes_decision_counter() -> None:
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "rollback_decision_requests_total" in response.text
