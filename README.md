# Release Rollback Decision Service

Deterministic release-gate service for deciding whether a production rollout should
continue, pause, or roll back based on incident and deployment evidence.

The project is shaped like a small platform/SRE service: one shared evaluator powers
both a CLI and FastAPI endpoint, exposes Prometheus metrics, includes deterministic
fixtures, and ships Kubernetes/Terraform scaffolding for a realistic deployment story.

## Architecture

```
release evidence JSON
        |
        v
shared evaluator in src/release_rollback/
        |
        +-- CLI: rollback-decision samples/risky_release.json
        |
        +-- API: POST /evaluate
        |
        +-- API: POST /review for multi-window post-deploy reviews
        |
        +-- CLI/API: audit approval records before release execution
        |
        +-- API: POST /audit for approval-evidence checks
        |
        +-- Metrics: /metrics
```

The evaluator is intentionally rule-based instead of pretending to use live production
data or a trained model. It scores signals that release managers and SREs actually
look at during a progressive rollout:

- current error rate versus baseline
- P95 latency regression
- resource saturation
- synthetic check failures
- customer impact count
- open Sev1 incident state
- change-freeze state
- traffic shift speed
- multi-window post-deploy evidence, when a release needs a rollback review

## What This Demonstrates

- CI/CD release-gate thinking with deterministic pass/fail behavior.
- Production-support judgment for rollback, pause, and continue decisions.
- API and CLI parity from one shared implementation.
- Post-deploy evidence review with JSON and Markdown output.
- Explicit rollback authorization, operator readiness, and tamper-evident evidence fingerprints.
- Approval audit gates for change tickets, evidence links, incident command, and overrides.
- FastAPI validation with Pydantic models.
- Prometheus metrics for decision counts and risk scores.
- Kubernetes manifests with probes, resource bounds, and scrape annotations.
- Terraform scaffold for immutable ECR image storage.
- Clear local verification without claiming unrun cloud or Docker validation.

## Setup

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

Or:

```bash
make setup
```

## Run The CLI

Safe release:

```bash
rollback-decision samples/safe_release.json
```

Risky release, with a report written to disk:

```bash
rollback-decision samples/risky_release.json --output reports/risky_release_report.json
```

Release-gate mode, where rollback exits with code `2`:

```bash
rollback-decision samples/risky_release.json --fail-on-rollback
```

Post-deploy review mode, where any rollback-worthy window exits with code `2`:

```bash
rollback-decision review samples/post_deploy_review.json \
  --output reports/post_deploy_review.json \
  --markdown reports/post_deploy_review.md \
  --fail-on-rollback
```

Approval audit mode, where incomplete release records exit with code `2`:

```bash
rollback-decision audit samples/approval_audit.json \
  --output reports/approval_audit.json \
  --markdown reports/approval_audit.md \
  --fail-on-block
```

## Run The API

```bash
uvicorn app.main:app --reload --port 8080
```

Then:

```bash
curl -s http://127.0.0.1:8080/healthz
curl -s -X POST http://127.0.0.1:8080/evaluate \
  -H 'content-type: application/json' \
  --data @samples/risky_release.json
curl -s -X POST http://127.0.0.1:8080/review \
  -H 'content-type: application/json' \
  --data @samples/post_deploy_review.json
curl -s -X POST http://127.0.0.1:8080/audit \
  -H 'content-type: application/json' \
  --data @samples/approval_audit.json
curl -s http://127.0.0.1:8080/metrics
```

For a local in-process API smoke test:

```bash
python scripts/api_smoke.py
```

## Verification

```bash
ruff check .
pytest
rollback-decision samples/safe_release.json
rollback-decision samples/risky_release.json --output reports/risky_release_report.json
make review-report
make audit-report
python scripts/api_smoke.py
```

Expected sample behavior:

- `samples/safe_release.json` recommends `continue`.
- `samples/risky_release.json` recommends `rollback`.
- `samples/post_deploy_review.json` reviews three windows and recommends `rollback`.
- `reports/post_deploy_review.md` is a tracked example report for a release record.
- `reports/approval_audit.md` shows a release record ready for execution.
- Rollback reviews remain `approval_required` until an explicit authorization record is supplied.
- `/metrics` exposes `rollback_decision_requests_total`,
  `rollback_decision_reviews_total`, `rollback_decision_approval_audits_total`,
  `rollback_execution_readiness_total`, and `rollback_decision_score`.

## Docker

Docker support is included for local users who have Docker installed:

```bash
docker compose up --build
```

This run did not require Docker to verify the Python package, CLI, tests, or API smoke.

## Kubernetes And Terraform

- `infra/kubernetes/deployment.yaml` provides a deployment and service with health probes,
  resource requests/limits, and Prometheus scrape annotations.
- `infra/terraform/main.tf` defines an immutable AWS ECR repository scaffold with image
  scanning enabled.

These assets are intentionally small. They show the deployment shape without claiming
access to a live cluster or AWS account.

## GitHub Actions

The CI example is stored at `docs/github-actions/ci.yml`.

To enable it in GitHub, copy it to `.github/workflows/ci.yml` after authenticating the
GitHub CLI with workflow scope:

```bash
gh auth refresh -h github.com -s workflow
```

## Limitations

- This is a deterministic decision engine, not a replacement for incident command.
- Thresholds are examples and should be tuned per service SLO and rollback cost.
- It does not query live metrics backends. Evidence is supplied as JSON so tests and
  release-gate behavior stay repeatable.
- Post-deploy review timestamps are supplied by the manifest and are not verified
  against a deployment system.
- Evidence fingerprints detect changed review inputs; they are not a substitute for an
  append-only audit store or cryptographic signature.
- Approval records are validated structurally; this sample does not verify external ticket,
  incident, or identity systems.
- Kubernetes and Terraform files are scaffolding and were not applied to a live account.

## Case Study

See [docs/CASE_STUDY.md](docs/CASE_STUDY.md) for the design note and operational scenario.
