# Component creation

Angular components are standalone. Do not add NgModules.

## Feature component

1. Create `frontend/src/app/features/<feature>/<name>.component.ts`.
2. Set `standalone: true` and list every imported symbol in `imports`.
3. Inject dependencies with `inject()`. Prefer `signal()`, `computed()`, and `input()` for UI state.
4. Use `@if`, `@for`, and `@switch` in templates. Do not use `*ngIf` or `*ngFor`.
5. Keep the component focused: one screen or one clear UI block. Move HTTP calls to a service in `core/` or the feature folder.
6. Register a lazy route in `app.routes.ts` with `loadComponent`.
7. Protect it with `authGuard` and `roleGuard` when a signed-in role is required. Add the same role check on the API.

## Reactive forms

Use `FormBuilder` / `NonNullableFormBuilder` with explicit types. Surface API errors in a signal. Do not store tokens in form state.

## Backend endpoint

1. Add a Pydantic v2 schema in `backend/app/schemas/`.
2. Put business logic in `backend/app/services/`.
3. Add a thin route in `backend/app/api/v1/endpoints/`.
4. Declare `response_model` and annotate the return type.
5. Use `async def` for database and HTTP work.
6. Enforce auth with `CurrentUser` or `require_roles(...)`.
7. Add a pytest in `backend/tests/api/` for the happy path and the relevant 401, 403, 404, or 422 case.
8. Update `docs/08-api-contracts.md` and `docs/09-role-permission-matrix.md` in the same change.
