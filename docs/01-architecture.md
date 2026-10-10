# Architecture

HRMS is a monorepo. The backend is the only source of truth for authentication, authorization, and business rules. The Angular app is a thin client.

The business planning document does not define a folder tree. This file is the source of truth for layout.

## Layout

```
backend/                 FastAPI application
  app/
    main.py              App factory, CORS, router mount
    core/                Settings and password/JWT helpers
    db/                  Async engine, session, declarative base
    models/              SQLAlchemy models
    schemas/             Pydantic v2 request and response models
    api/deps.py          Session, current user, role dependencies
    api/v1/endpoints/    HTTP routes
    services/            Business logic
    seed.py              Dev user seed
  alembic/               Schema migrations
  tests/                 pytest
frontend/                Angular standalone app
  src/app/core/          Auth, interceptor, guards
  src/app/features/      Login and role home screens
  src/app/shared/        Shell layout
  proxy.conf.json        Dev proxy /api -> :8000
docs/                    Living documentation
.cursor/rules/           Agent conventions
docker-compose.yml       Local PostgreSQL
```

There is no shared runtime package. Align types by hand: Pydantic schemas on the server, TypeScript interfaces on the client.

## Runtime

- API prefix: `/api/v1`
- Backend dev server: `http://localhost:8000`
- Angular dev server: `http://localhost:4200`
- Dev HTTP calls use relative `/api/v1/...`. `frontend/proxy.conf.json` forwards `/api` to the API so the refresh cookie is same-origin.
- PostgreSQL is the only application database. Local Compose service: user `hrms`, database `hrms`, port `5432`.

## Auth model

- Access JWT: JSON body, held in an Angular signal. Never written to `localStorage` or `sessionStorage`.
- Refresh JWT: `HttpOnly` cookie, `SameSite=Lax`, path `/api/v1/auth`. `Secure` is on only when `REFRESH_COOKIE_SECURE=true`.
- Refresh tokens are stored as SHA-256 hashes and rotated on every refresh.
- Roles: `admin`, `manager`, `employee`. Protected routes use `get_current_user` and `require_roles`. Route guards only hide pages.

## Request path

1. Router validates the body with a Pydantic schema.
2. Dependencies open a session and, when required, resolve the current user and role.
3. A service performs the work and flushes.
4. The session dependency commits on success and rolls back on exception.
5. The router returns a response schema.

## Not in this foundation

Payroll and full production deployment (TLS, secrets manager, horizontal scale) are out of scope for this MVP. Documents use local disk; notifications are in-app only. CI runs in `.github/workflows/ci.yml`; the API image is built from `backend/Dockerfile`. See `docs/06-follow-ups-and-roadmap.md`.
