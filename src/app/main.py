from __future__ import annotations

from fastapi import FastAPI, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from release_rollback import ReleaseEvidence, evaluate_release

app = FastAPI(
    title="Release Rollback Decision Service",
    version="0.1.0",
    description="Deterministic release gate for progressive delivery and incident response.",
)

DECISIONS = Counter(
    "rollback_decision_requests_total",
    "Release rollback decision requests by final recommendation.",
    ["decision"],
)
SCORES = Histogram(
    "rollback_decision_score",
    "Rollback decision risk score.",
    buckets=(0, 10, 25, 35, 50, 70, 90, 120),
)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/evaluate")
def evaluate(evidence: ReleaseEvidence):
    report = evaluate_release(evidence)
    DECISIONS.labels(report.decision).inc()
    SCORES.observe(report.score)
    return report


@app.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
