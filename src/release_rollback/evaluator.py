from __future__ import annotations

import hashlib

from .models import (
    ApprovalAuditReport,
    ApprovalAuditRequest,
    DecisionReport,
    PostDeployReviewReport,
    PostDeployReviewRequest,
    ReleaseEvidence,
    ReviewedWindow,
    Severity,
    TriggeredRule,
)


def _rule(rule: str, points: int, message: str) -> TriggeredRule:
    return TriggeredRule(rule=rule, points=points, message=message)


def evaluate_release(evidence: ReleaseEvidence) -> DecisionReport:
    rules: list[TriggeredRule] = []

    error_delta = evidence.error_rate_percent - evidence.baseline_error_rate_percent
    latency_ratio = (
        evidence.p95_latency_ms / evidence.baseline_p95_latency_ms
        if evidence.baseline_p95_latency_ms > 0
        else 1.0
    )

    if evidence.open_sev1_incident:
        rules.append(_rule("sev1-open", 45, "A Sev1 incident is open during the rollout."))
    if evidence.customer_impact_count >= 25:
        rules.append(
            _rule(
                "customer-impact",
                35,
                f"{evidence.customer_impact_count} impacted customers were reported.",
            )
        )
    elif evidence.customer_impact_count > 0:
        rules.append(
            _rule(
                "limited-customer-impact",
                18,
                f"{evidence.customer_impact_count} customers were reported as impacted.",
            )
        )
    if error_delta >= 3.0 or evidence.error_rate_percent >= 5.0:
        rules.append(
            _rule(
                "error-budget-burn",
                30,
                f"Error rate is {evidence.error_rate_percent:.2f}% "
                f"versus {evidence.baseline_error_rate_percent:.2f}% baseline.",
            )
        )
    elif error_delta >= 1.0:
        rules.append(
            _rule("error-rate-regression", 16, f"Error rate rose by {error_delta:.2f} points.")
        )
    if latency_ratio >= 1.8:
        rules.append(
            _rule(
                "latency-regression",
                20,
                f"P95 latency is {latency_ratio:.1f}x baseline.",
            )
        )
    if evidence.saturation_percent >= 90:
        rules.append(
            _rule(
                "resource-saturation",
                18,
                f"Resource saturation is {evidence.saturation_percent:.1f}%.",
            )
        )
    if evidence.failed_synthetic_checks >= 3:
        rules.append(
            _rule(
                "synthetic-check-failures",
                18,
                f"{evidence.failed_synthetic_checks} synthetic checks failed.",
            )
        )
    elif evidence.failed_synthetic_checks > 0:
        rules.append(
            _rule(
                "synthetic-check-warning",
                8,
                f"{evidence.failed_synthetic_checks} synthetic check failed.",
            )
        )
    if evidence.change_freeze_active:
        rules.append(_rule("change-freeze", 12, "A change freeze is active."))
    if evidence.deployment_age_minutes < 10 and evidence.canary_traffic_percent >= 50:
        rules.append(
            _rule(
                "rapid-traffic-shift",
                10,
                "Traffic reached at least 50% in the first 10 minutes.",
            )
        )

    score = sum(rule.points for rule in rules)
    if score >= 70 or any(rule.rule == "sev1-open" for rule in rules):
        decision = "rollback"
        severity = "critical" if score >= 80 else "high"
    elif score >= 35:
        decision = "pause"
        severity = "medium"
    else:
        decision = "continue"
        severity = "low"

    actions = _actions_for(decision, evidence)
    summary = (
        f"{evidence.service} {evidence.version} in {evidence.environment}: "
        f"{decision} recommended with score {score}."
    )

    return DecisionReport(
        service=evidence.service,
        environment=evidence.environment,
        version=evidence.version,
        decision=decision,
        severity=severity,
        score=score,
        triggered_rules=rules,
        recommended_actions=actions,
        summary=summary,
    )


def _actions_for(decision: str, evidence: ReleaseEvidence) -> list[str]:
    actions = [
        "Attach this report to the deployment record.",
        "Keep the incident channel updated with the current decision and owner.",
    ]
    if decision == "rollback":
        actions.extend(
            [
                "Stop traffic increase and execute the rollback runbook.",
                "Capture the failing version, metrics window, and customer impact before cleanup.",
                "Run post-rollback health checks before closing the incident.",
            ]
        )
    elif decision == "pause":
        actions.extend(
            [
                "Hold the rollout at the current traffic percentage.",
                "Recheck error rate, latency, and synthetic checks after one observation window.",
                "Escalate to rollback if impact or error budget burn increases.",
            ]
        )
    else:
        actions.extend(
            [
                "Continue the rollout using the normal progressive delivery schedule.",
                "Keep monitoring the same signals until the release reaches 100%.",
            ]
        )
    if evidence.runbook_url:
        actions.append(f"Use runbook: {evidence.runbook_url}")
    return actions


def review_post_deploy_evidence(request: PostDeployReviewRequest) -> PostDeployReviewReport:
    window_reports = [
        (window.observed_at, evaluate_release(window.evidence)) for window in request.windows
    ]
    decisions = [report.decision for _, report in window_reports]
    severities = [report.severity for _, report in window_reports]
    max_score = max(report.score for _, report in window_reports)
    latest_report = window_reports[-1][1]

    if "rollback" in decisions:
        decision = "rollback"
    elif "pause" in decisions:
        decision = "pause"
    else:
        decision = "continue"

    severity = _max_severity(severities)
    first_evidence = request.windows[0].evidence
    reviewed_windows = [
        ReviewedWindow(
            observed_at=observed_at,
            decision=report.decision,
            severity=report.severity,
            score=report.score,
            triggered_rules=[rule.rule for rule in report.triggered_rules],
            summary=report.summary,
        )
        for observed_at, report in window_reports
    ]
    rollback_windows = decisions.count("rollback")
    pause_windows = decisions.count("pause")
    execution_status = (
        "approval_required"
        if decision == "rollback" and request.rollback_approval is None
        else "ready"
    )
    evidence_fingerprint = hashlib.sha256(
        request.model_dump_json(exclude={"rollback_approval"}).encode("utf-8")
    ).hexdigest()
    summary = (
        f"{request.release_id}: {decision} after {len(window_reports)} post-deploy "
        f"window(s); max score {max_score}, latest score {latest_report.score}."
    )

    return PostDeployReviewReport(
        release_id=request.release_id,
        service=first_evidence.service,
        environment=first_evidence.environment,
        version=first_evidence.version,
        owner=request.owner,
        decision=decision,
        severity=severity,
        max_score=max_score,
        latest_score=latest_report.score,
        window_count=len(window_reports),
        rollback_windows=rollback_windows,
        pause_windows=pause_windows,
        execution_status=execution_status,
        evidence_fingerprint=evidence_fingerprint,
        rollback_approval=request.rollback_approval,
        reviewed_windows=reviewed_windows,
        recommended_actions=_review_actions(decision, request, latest_report),
        summary=summary,
    )


def render_markdown_review(report: PostDeployReviewReport) -> str:
    lines = [
        f"# Rollback Decision Review: {report.release_id}",
        "",
        f"- Service: `{report.service}`",
        f"- Environment: `{report.environment}`",
        f"- Version: `{report.version}`",
        f"- Owner: `{report.owner}`",
        f"- Decision: `{report.decision}`",
        f"- Severity: `{report.severity}`",
        f"- Windows reviewed: `{report.window_count}`",
        f"- Max score: `{report.max_score}`",
        f"- Latest score: `{report.latest_score}`",
        f"- Execution status: `{report.execution_status}`",
        f"- Evidence fingerprint: `{report.evidence_fingerprint}`",
        "",
        "## Summary",
        "",
        report.summary,
        "",
        "## Reviewed Windows",
        "",
        "| Observed At | Decision | Severity | Score | Rules |",
        "| --- | --- | --- | ---: | --- |",
    ]
    for window in report.reviewed_windows:
        rules = ", ".join(window.triggered_rules) if window.triggered_rules else "none"
        lines.append(
            f"| {window.observed_at} | {window.decision} | {window.severity} | "
            f"{window.score} | {rules} |"
        )

    lines.extend(["", "## Rollback Authorization", ""])
    if report.rollback_approval:
        lines.extend(
            [
                f"- Approved by: `{report.rollback_approval.approved_by}`",
                f"- Approved at: `{report.rollback_approval.approved_at}`",
                f"- Change ticket: `{report.rollback_approval.change_ticket}`",
                f"- Reason: {report.rollback_approval.reason}",
            ]
        )
    else:
        lines.append("- No rollback authorization was supplied.")

    lines.extend(["", "## Recommended Actions", ""])
    lines.extend(f"- {action}" for action in report.recommended_actions)
    return "\n".join(lines) + "\n"


def review_approval_audit(request: ApprovalAuditRequest) -> ApprovalAuditReport:
    review = review_post_deploy_evidence(request.review)
    checks = {
        "action_matches_recommendation": request.approved_action == review.decision,
        "change_ticket_present": bool(request.change_ticket.strip()),
        "evidence_attached": len(request.evidence_links) >= 2,
        "incident_commander_present": bool(request.incident_commander),
        "override_documented": (
            request.approved_action == review.decision or bool(request.override_reason)
        ),
    }
    required_checks = ["change_ticket_present", "evidence_attached"]
    if review.decision == "rollback":
        required_checks.append("incident_commander_present")
    if request.approved_action != review.decision:
        required_checks.append("override_documented")

    findings = {
        "action_matches_recommendation": "Approved action differs from the evidence recommendation.",
        "change_ticket_present": "A change ticket is required for the audit record.",
        "evidence_attached": "Attach at least two evidence links to preserve decision context.",
        "incident_commander_present": "Rollback approval requires an incident commander.",
        "override_documented": "An override reason is required when approval differs from evidence.",
    }
    failed = [name for name in required_checks if not checks[name]]
    if not checks["action_matches_recommendation"]:
        failed.insert(0, "action_matches_recommendation")
    status = "block" if failed else "ready"
    summary = (
        f"{request.review.release_id}: approval audit {status}; evidence recommends "
        f"{review.decision}, approved action is {request.approved_action}."
    )
    return ApprovalAuditReport(
        release_id=request.review.release_id,
        recommended_action=review.decision,
        approved_action=request.approved_action,
        status=status,
        approver=request.approver,
        approved_at=request.approved_at,
        change_ticket=request.change_ticket,
        evidence_count=len(request.evidence_links),
        checks=checks,
        findings=[findings[name] for name in failed],
        summary=summary,
    )


def render_markdown_audit(report: ApprovalAuditReport) -> str:
    lines = [
        f"# Release Approval Audit: {report.release_id}",
        "",
        f"- Status: `{report.status}`",
        f"- Recommended action: `{report.recommended_action}`",
        f"- Approved action: `{report.approved_action}`",
        f"- Approver: `{report.approver}`",
        f"- Approved at: `{report.approved_at}`",
        f"- Change ticket: `{report.change_ticket}`",
        f"- Evidence links: `{report.evidence_count}`",
        "",
        "## Checks",
        "",
    ]
    lines.extend(
        f"- {name}: `{'pass' if passed else 'fail'}`" for name, passed in report.checks.items()
    )
    lines.extend(["", "## Findings", ""])
    lines.extend(f"- {finding}" for finding in report.findings)
    if not report.findings:
        lines.append("- None. The approval record is ready to attach to the release.")
    return "\n".join(lines) + "\n"


def _max_severity(severities: list[Severity]) -> Severity:
    order: dict[Severity, int] = {"low": 0, "medium": 1, "high": 2, "critical": 3}
    return max(severities, key=lambda severity: order[severity])


def _review_actions(
    decision: str,
    request: PostDeployReviewRequest,
    latest_report: DecisionReport,
) -> list[str]:
    actions = [
        "Attach this review to the release record with the observation window list.",
        "Post the final decision and owner in the incident or deployment channel.",
    ]
    if decision == "rollback":
        if request.rollback_approval is None:
            actions.append("Obtain explicit rollback authorization before execution.")
        actions.extend(
            [
                "Stop further promotion and start the rollback runbook.",
                "Compare the latest window against the highest-risk window before closing impact.",
                "Keep customer-impact and synthetic-check evidence with the rollback timeline.",
            ]
        )
    elif decision == "pause":
        actions.extend(
            [
                "Hold traffic at the current level and collect one more observation window.",
                "Escalate to rollback if the next window adds impact or error-budget burn.",
            ]
        )
    else:
        actions.extend(
            [
                "Continue progressive delivery while retaining the reviewed windows.",
                "Keep the same signals on watch until the release reaches full traffic.",
            ]
        )
    actions.extend(latest_report.recommended_actions[:2])
    if request.rollback_runbook_url:
        actions.append(f"Rollback runbook: {request.rollback_runbook_url}")
    return actions
