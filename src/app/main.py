from __future__ import annotations

from fastapi import FastAPI, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from release_rollback import (
    ApprovalAuditRequest,
    PostDeployReviewRequest,
    ReleaseEvidence,
    evaluate_release,
)
from release_rollback.evaluator import review_approval_audit, review_post_deploy_evidence

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
REVIEWS = Counter(
    "rollback_decision_reviews_total",
    "Post-deploy rollback review requests by final recommendation.",
    ["decision"],
)
AUDITS = Counter(
    "rollback_decision_approval_audits_total",
    "Release approval audit reviews by readiness status.",
    ["status"],
)
EXECUTION_READINESS = Counter(
    "rollback_execution_readiness_total",
    "Post-deploy reviews by rollback execution readiness.",
    ["status"],
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


@app.post("/review")
def review(request: PostDeployReviewRequest):
    report = review_post_deploy_evidence(request)
    REVIEWS.labels(report.decision).inc()
    EXECUTION_READINESS.labels(report.execution_status).inc()
    SCORES.observe(report.max_score)
    return report


@app.post("/audit")
def audit(request: ApprovalAuditRequest):
    report = review_approval_audit(request)
    AUDITS.labels(report.status).inc()
    return report


@app.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
