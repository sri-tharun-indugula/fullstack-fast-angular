# Shared components

## Frontend

| Location | What belongs there |
| --- | --- |
| `src/app/core/` | Singletons: auth service, HTTP interceptor, guards, user types |
| `src/app/shared/` | Reusable UI with no feature rules. The authenticated shell lives here. |
| `src/app/features/` | Screens owned by one product area |

Shared components stay standalone and presentational. They receive data through `input()` and emit through `output()`. They do not call `/api` directly.

The shell reads `AuthService.user` and shows nav links the current role may open. That filter is UX. The API still rejects forbidden calls.

Angular Material is the component library (toolbar, card, form field, button, snack-free inline errors for now).

## Backend

Shared server code lives in:

- `app/core/` for settings and cryptography
- `app/api/deps.py` for session and auth dependencies
- `app/schemas/` for types reused by more than one route

Do not import `frontend/` from `backend/` or the reverse.
