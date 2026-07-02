# Case Study: Rollback Decisions During Progressive Delivery

## Problem

Release incidents are often messy because teams mix live metrics, customer reports,
deployment timing, and incomplete synthetic checks while pressure is rising. A good
release gate should not hide the decision logic. It should make the rollback reasoning
repeatable, reviewable, and easy to attach to a deployment or incident record.

## Approach

This project uses a deterministic scoring engine. Each evidence field can trigger one
or more named rules. The final score maps to:

- `continue` for normal rollout progress.
- `pause` when the release needs another observation window.
- `rollback` when impact or risk is high enough to stop the rollout.

The same engine powers:

- `rollback-decision`, a CLI suitable for CI/CD gates.
- `rollback-decision review`, a post-deploy evidence review that turns multiple
  observation windows into JSON and Markdown release records.
- `POST /evaluate`, a FastAPI route suitable for internal release tooling.
- `POST /review`, the API equivalent of the multi-window review.
- `/metrics`, a Prometheus endpoint that tracks decision volume and risk scores.

## Example Scenario

`samples/risky_release.json` models a checkout API canary where:

- a Sev1 incident is open,
- error rate exceeds baseline,
- P95 latency regressed,
- resource saturation is high,
- synthetic checks are failing,
- customer impact is already visible,
- traffic reached 60% within seven minutes.

The evaluator recommends `rollback` and returns the triggered rule names with suggested
next actions. This is the kind of artifact an on-call engineer could attach to a
deployment timeline or incident summary.

`samples/post_deploy_review.json` extends the scenario across three observation windows.
The first window can continue, the second pauses, and the final window rolls back after
the incident becomes customer-visible. `reports/post_deploy_review.md` is the
recruiter-readable artifact this project would attach to a deployment record.

## Why It Is Useful

The value is not in pretending the thresholds are universal. The value is in the
operational shape:

- evidence is structured,
- rules are named,
- output is deterministic,
- CLI and API behavior match,
- CI can fail a risky rollout,
- post-deploy reviews preserve the decision timeline,
- metrics make gate behavior observable over time.

## Production Hardening Ideas

- Pull evidence from Prometheus, Datadog, or CloudWatch instead of JSON.
- Make thresholds service-specific through signed configuration.
- Store reports in object storage or the deployment system.
- Require an explicit override reason when humans continue after `rollback`.
- Emit structured audit logs for compliance-sensitive release environments.
