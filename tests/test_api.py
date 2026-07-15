import json

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


def test_review_endpoint_summarizes_post_deploy_windows() -> None:
    payload = {
        "release_id": "checkout-api-2026.06.24-rc3",
        "owner": "release-captain",
        "windows": [
            {
                "observed_at": "2026-06-24T10:05:00Z",
                "evidence": {
                    "service": "checkout-api",
                    "environment": "production",
                    "version": "2026.06.24-rc3",
                    "deployment_age_minutes": 42,
                    "error_rate_percent": 0.7,
                    "baseline_error_rate_percent": 0.6,
                    "p95_latency_ms": 430,
                    "baseline_p95_latency_ms": 410,
                    "saturation_percent": 63,
                    "failed_synthetic_checks": 0,
                    "canary_traffic_percent": 25,
                    "customer_impact_count": 0,
                    "open_sev1_incident": False,
                    "change_freeze_active": False,
                },
            },
            {
                "observed_at": "2026-06-24T10:18:00Z",
                "evidence": {
                    "service": "checkout-api",
                    "environment": "production",
                    "version": "2026.06.24-rc3",
                    "deployment_age_minutes": 18,
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
                },
            },
        ],
    }

    response = client.post("/review", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["decision"] == "rollback"
    assert body["window_count"] == 2
    assert body["rollback_windows"] == 1
    assert body["execution_status"] == "approval_required"
    assert len(body["evidence_fingerprint"]) == 64


def test_metrics_endpoint_exposes_decision_counter() -> None:
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "rollback_decision_requests_total" in response.text
    assert "rollback_decision_reviews_total" in response.text
    assert "rollback_decision_approval_audits_total" in response.text
    assert "rollback_execution_readiness_total" in response.text


def test_audit_endpoint_validates_approval_evidence() -> None:
    payload = json.loads(open("samples/approval_audit.json", encoding="utf-8").read())

    response = client.post("/audit", json=payload)

    assert response.status_code == 200
    assert response.json()["status"] == "ready"
