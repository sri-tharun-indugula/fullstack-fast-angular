# Code review checklist

## API

- Protected route depends on `get_current_user` or `require_roles`.
- Response model excludes password hashes and refresh token hashes.
- Pydantic v2 style only.
- New or changed behavior has a pytest for success and for 401 or 403 when auth applies.
- Alembic revision exists for every model change.

## Angular

- Component is standalone and uses `inject()`, signals, and `@if` / `@for`.
- No `any`. No token written to `localStorage` or `sessionStorage`.
- HTTP calls go through `HttpClient` and the auth interceptor.
- Role checks in guards match `docs/09-role-permission-matrix.md` and are duplicated on the server.

## Secrets and docs

- `.env` is not in the diff. `.env.example` has empty secrets.
- `docs/08-api-contracts.md` and `docs/09-role-permission-matrix.md` match the change.
- Open questions are recorded in `docs/06-follow-ups-and-roadmap.md`.
