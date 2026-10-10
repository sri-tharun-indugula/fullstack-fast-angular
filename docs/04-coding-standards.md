# Coding standards

## TypeScript

- No `any`. Type HTTP responses with interfaces in `core/auth/auth.models.ts` or a feature `*.models.ts`.
- Prefer `inject()` over constructor parameters.
- Prefer signals for synchronous UI state. Use RxJS for HTTP.
- Keep components, services, and endpoints small. Extract a helper when a second caller needs it.

## Python

- Pydantic v2 only: `ConfigDict`, `Field`, `field_validator`, `model_validate`, `model_dump`. Do not use `class Config` or `orm_mode`.
- Type function arguments and returns. Avoid untyped `dict` payloads at the boundary; use models.
- `async def` for I/O. Plain `def` for hashing, JWT claim building, and other CPU-only helpers.
- Raise `HTTPException` for expected client errors. Do not return stack traces.

## Security defaults

- Secrets come from the environment via `pydantic-settings`.
- Passwords are hashed with Argon2 (`pwdlib`). Never log passwords, tokens, or `Authorization` headers.
- The access token stays in memory. The refresh token stays in an httpOnly cookie.

## Commits

Use Conventional Commits, for example `feat(auth): add refresh-token rotation`.
