from release_rollback import PostDeployReviewRequest, ReleaseEvidence, evaluate_release
from release_rollback.evaluator import render_markdown_review, review_post_deploy_evidence


def test_risky_release_recommends_rollback() -> None:
    evidence = ReleaseEvidence.model_validate_json(
        open("samples/risky_release.json", encoding="utf-8").read()
    )

    report = evaluate_release(evidence)

    assert report.decision == "rollback"
    assert report.severity in {"high", "critical"}
    assert report.score >= 70
    assert {rule.rule for rule in report.triggered_rules} >= {
        "sev1-open",
        "customer-impact",
        "error-budget-burn",
    }


def test_safe_release_continues() -> None:
    evidence = ReleaseEvidence.model_validate_json(
        open("samples/safe_release.json", encoding="utf-8").read()
    )

    report = evaluate_release(evidence)

    assert report.decision == "continue"
    assert report.score == 0
    assert report.triggered_rules == []


def test_pause_for_medium_risk_without_customer_impact() -> None:
    evidence = ReleaseEvidence(
        service="billing-api",
        environment="production",
        version="2026.06.24",
        deployment_age_minutes=18,
        error_rate_percent=2.4,
        baseline_error_rate_percent=0.8,
        p95_latency_ms=700,
        baseline_p95_latency_ms=380,
        saturation_percent=72,
        failed_synthetic_checks=2,
        canary_traffic_percent=30,
        customer_impact_count=0,
    )

    report = evaluate_release(evidence)

    assert report.decision == "pause"
    assert report.severity == "medium"
    assert "Hold the rollout" in " ".join(report.recommended_actions)


def test_post_deploy_review_rolls_back_when_later_window_worsens() -> None:
    request = PostDeployReviewRequest.model_validate_json(
        open("samples/post_deploy_review.json", encoding="utf-8").read()
    )

    report = review_post_deploy_evidence(request)
    markdown = render_markdown_review(report)

    assert report.decision == "rollback"
    assert report.window_count == 3
    assert report.rollback_windows == 1
    assert report.max_score >= report.latest_score >= 70
    assert "checkout-api-2026.06.24-rc3" in markdown
    assert "| 2026-06-24T18:18:00Z | rollback |" in markdown
