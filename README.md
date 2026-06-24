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

## What This Demonstrates

- CI/CD release-gate thinking with deterministic pass/fail behavior.
- Production-support judgment for rollback, pause, and continue decisions.
- API and CLI parity from one shared implementation.
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
python scripts/api_smoke.py
```

Expected sample behavior:

- `samples/safe_release.json` recommends `continue`.
- `samples/risky_release.json` recommends `rollback`.
- `/metrics` exposes `rollback_decision_requests_total` and `rollback_decision_score`.

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
- Kubernetes and Terraform files are scaffolding and were not applied to a live account.

## Case Study

See [docs/CASE_STUDY.md](docs/CASE_STUDY.md) for the design note and operational scenario.
