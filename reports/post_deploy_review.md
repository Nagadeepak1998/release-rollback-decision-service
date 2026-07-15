# Rollback Decision Review: checkout-api-2026.06.24-rc3

- Service: `checkout-api`
- Environment: `production`
- Version: `2026.06.24-rc3`
- Owner: `release-captain`
- Decision: `rollback`
- Severity: `critical`
- Windows reviewed: `3`
- Max score: `166`
- Latest score: `166`
- Execution status: `ready`
- Evidence fingerprint: `f2bf53ec5d209ca4dc3a05154c83a83cfacf527eec64ece60dd0fe66e4276fd9`

## Summary

checkout-api-2026.06.24-rc3: rollback after 3 post-deploy window(s); max score 166, latest score 166.

## Reviewed Windows

| Observed At | Decision | Severity | Score | Rules |
| --- | --- | --- | ---: | --- |
| 2026-06-24T18:05:00Z | continue | low | 8 | synthetic-check-warning |
| 2026-06-24T18:12:00Z | pause | medium | 62 | limited-customer-impact, error-rate-regression, latency-regression, synthetic-check-warning |
| 2026-06-24T18:18:00Z | rollback | critical | 166 | sev1-open, customer-impact, error-budget-burn, latency-regression, resource-saturation, synthetic-check-failures |

## Rollback Authorization

- Approved by: `incident-commander@example.invalid`
- Approved at: `2026-06-24T18:20:00Z`
- Change ticket: `CHG-2026-0624-117`
- Reason: Customer impact and the open Sev1 require immediate rollback.

## Recommended Actions

- Attach this review to the release record with the observation window list.
- Post the final decision and owner in the incident or deployment channel.
- Stop further promotion and start the rollback runbook.
- Compare the latest window against the highest-risk window before closing impact.
- Keep customer-impact and synthetic-check evidence with the rollback timeline.
- Attach this report to the deployment record.
- Keep the incident channel updated with the current decision and owner.
- Rollback runbook: https://runbooks.example.invalid/checkout-api/rollback
