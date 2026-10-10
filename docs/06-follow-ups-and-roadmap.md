# Follow-ups and roadmap

The business plan's Phase 1 is Employee Master, Attendance, Leave, and basic self-service. This repo contains the technical foundation plus an MVP for employee profiles and departments.

## Build order

| Order | Scope | Status |
| --- | --- | --- |
| 1 | Foundation: structure, docs, rules, JWT auth, roles, login shell | Done |
| 2 | Employee profile and organization structure | Done (MVP: departments, profiles, self-service contact fields, manager team list) |
| 3 | Leave: apply, then approve or reject | Done (MVP: single-level manager approval, balances, cancel pending) |
| 4 | Attendance | Done (MVP: web check-in/out, history, manager team view by date) |
| 5 | Performance, goals, reviews | Done (MVP: assign goals, employee progress, manager team view) |
| 6 | Documents and notifications | Done (MVP: company/employee docs, in-app notifications for leave/goals/docs) |
| 7 | Audit logs, reporting, production hardening | Done (MVP: audit trail, admin/manager reports, auth rate limit, CI, API Dockerfile) |

Payroll, recruitment, learning, benefits, and AI features stay behind those items. They match later phases in the business plan.

## Open questions

- Leave approval chain: **MVP uses single direct manager** (`employee_profiles.manager_user_id`); admin may approve any request. Multi-level chains are not implemented.
- India statutory payroll (PF, ESI, PT, TDS, Form 16): out of scope until payroll is scheduled.
- SSO (Azure AD, Google, Okta) and 2FA: required by the business NFR, not designed yet.
- Biometric, GPS, and geofenced attendance: not designed yet.
- Token storage for a future native mobile client: the cookie design assumes a browser on the same site as the API.

## Technical debt

- No org-chart visualization; departments are a flat list with optional `parent_id`.
- Admin cannot edit employee profiles in the UI yet (API supports `PATCH /employees/{user_id}`).
- Auth rate limiting is in-memory per process (not suitable for multi-instance without a shared store).
- No frontend production image or managed object storage for documents yet.
- Refresh reuse is rejected by rotation, but there is no reuse-detection family revoke beyond the single token row.
- Docker Compose is the intended local database. This environment may not have Docker installed; a local PostgreSQL instance on port 5432 is an acceptable substitute if it uses the same `DATABASE_URL`.
