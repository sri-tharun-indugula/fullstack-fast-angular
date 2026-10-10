# API contracts

Base path: `/api/v1`. JSON uses `Content-Type: application/json`. Authenticated calls send `Authorization: Bearer <access_token>`.

Cookie `refresh_token` (name configurable) is `HttpOnly`, path `/api/v1/auth`. Browsers send it only to login, refresh, and logout.

## Health

`GET /health` — public.

```json
{ "status": "ok" }
```

## Auth

### `POST /auth/login`

Body: `{ "email": "user@example.com", "password": "string" }`

Success `200`:

```json
{ "access_token": "<jwt>", "token_type": "bearer", "expires_in": 900 }
```

Also `Set-Cookie` for the refresh token. Failure `401` with `{ "detail": "Invalid email or password" }` for unknown email, bad password, or inactive user.

### `POST /auth/refresh`

No body. Requires the refresh cookie.

Success `200`: same token body as login, plus a rotated refresh cookie. The previous refresh token is revoked.

Failure `401` when the cookie is missing, expired, revoked, or reused.

### `POST /auth/logout`

No body. Revokes the refresh token when the cookie is valid, then clears the cookie. Always `204`.

### `GET /auth/me`

Requires an access token. Any active role.

```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "Name",
  "role": "admin"
}
```

`role` is `admin`, `manager`, or `employee`. `401` when the access token is missing or invalid.

## Role probe

`GET /admin/ping` — access token with role `admin` only.

```json
{ "status": "ok", "role": "admin" }
```

`403` for other roles. This route exists so role checks are covered before admin features exist.

## Departments

### `GET /departments`

Roles: `admin`, `manager`. Returns a flat list ordered by name.

### `POST /departments`

Role: `admin`. Body: `{ "name": "Engineering", "code": "ENG", "parent_id": null }`. `code` is stored uppercase. `201` on success. `409` when the code exists.

### `PATCH /departments/{department_id}`

Role: `admin`. Body may include `name` and/or `parent_id`.

## Employees

`EmployeePublic` includes user identity (`email`, `full_name`, `role`), HR fields, nested `department`, and `manager_full_name`.

### `GET /employees/me`

Any authenticated user with an employee profile. `404` when no profile exists.

### `PATCH /employees/me`

Employee self-service. Body: `{ "phone": "...", "work_location": "..." }`. Only contact fields; job data is admin-managed.

### `GET /employees`

`admin`: all profiles. `manager`: direct reports (`manager_user_id` equals the current user). `employee`: `403`.

### `GET /employees/{user_id}`

`admin`: any profile. `manager`: direct reports only. `employee`: own profile only.

### `POST /employees`

Role: `admin`. Creates a profile for an existing user without one.

### `PATCH /employees/{user_id}`

Role: `admin`. Updates department, manager, job title, employee code, contact fields, and `joined_on`.

## Leave

Leave days are **inclusive calendar days** within a single calendar year. Pending requests reserve balance in `pending`; approval moves days to `used`.

Approval: **direct manager** (`employee_profiles.manager_user_id`) or **admin**. No multi-level chain in this MVP.

### `GET /leave/types`

Any authenticated user. Active leave types only.

### `GET /leave/balances/me`

Any authenticated user with balances for the requested `year` (defaults to current year).

### `GET /leave/requests/me`

Lists the caller's leave requests, newest first.

### `POST /leave/requests`

Apply for leave. Body: `{ "leave_type_id", "start_date", "end_date", "reason" }`. `start_date` cannot be in the past. `422` when balance is insufficient.

### `POST /leave/requests/{id}/cancel`

Employee can cancel own **pending** request and release pending balance.

### `GET /leave/requests/inbox`

`admin`: all pending requests. `manager`: pending requests from direct reports.

### `POST /leave/requests/{id}/approve` and `/reject`

Body: optional `{ "note": "..." }`. Manager (direct report) or admin. `422` when not pending.

## Attendance

Work date is the **UTC calendar date** at check-in. One open row per user per day. Requires an employee profile.

### `GET /attendance/today`

Returns today's record or `null`.

### `POST /attendance/check-in`

Creates today's check-in. `409` if already checked in.

### `POST /attendance/check-out`

Sets check-out time for today. `404` without check-in; `409` if already checked out.

### `GET /attendance/me`

Query `from` and `to` dates (inclusive). Defaults to the last 30 days through today.

### `GET /attendance/team`

Query `date` (defaults to today UTC). `manager`: direct reports. `admin`: all employees with profiles.

## Goals

Performance goals are assigned to an employee (`assignee_user_id`). Status: `not_started`, `in_progress`, `completed`, `cancelled`.

### `GET /goals/me`

Goals assigned to the current user.

### `GET /goals/team`

`manager`: direct reports. `admin`: all goals.

### `GET /goals/{goal_id}`

Assignee, their manager, or admin.

### `POST /goals`

`manager` (direct reports only) or `admin`. Body includes `assignee_user_id`, `title`, `description`, optional `due_date`.

### `PATCH /goals/{goal_id}/self`

Assignee updates `progress_percent` and `status` (not `cancelled`).

### `PATCH /goals/{goal_id}`

Manager or admin may update all fields including `manager_note`.

## Documents

Files are stored on disk under `DOCUMENTS_STORAGE_PATH` (default `data/documents/`). Allowed types: PDF, plain text, PNG, JPEG. Max size defaults to 5 MB (`DOCUMENT_MAX_BYTES`).

Scope: `company` (all users with an employee profile) or `employee` (owner, their manager, and admin).

### `GET /documents/me`

Lists documents visible to the current user.

### `GET /documents/{document_id}/content`

Streams the file with `Content-Disposition` filename. Requires access per scope rules.

### `POST /documents`

`multipart/form-data`: `title`, `scope`, `file`, optional `description`, optional `owner_user_id` (required for employee scope when uploading for someone else). Admin may upload `company` documents. Employees may upload only `employee` scope for themselves. Managers may upload `employee` scope for direct reports or self.

### `DELETE /documents/{document_id}`

Admin or the original uploader.

## Notifications

In-app only (no email/SMS in this MVP). Created when leave is submitted (manager), approved/rejected (employee), a goal is assigned, or a document is shared.

### `GET /notifications/me`

Query `unread_only` (default false). Returns the latest 100 items.

### `GET /notifications/unread-count`

```json
{ "count": 2 }
```

### `PATCH /notifications/{notification_id}/read`

Marks one notification read for the current user.

### `POST /notifications/read-all`

`204` — marks all unread notifications read.

## Audit logs

Append-only records for security-sensitive actions. Admin only.

### `GET /admin/audit-logs`

Query `limit` (default 50, max 200), `offset`, optional `action` (e.g. `auth.login_success`, `leave.approved`).

## Reports

### `GET /reports/overview`

Admin only. Headcount by department, pending leave count, and how many employees checked in today (UTC).

### `GET /reports/team`

Admin or manager. For managers: direct reports only. For admin: same metrics across all employees.

## Auth rate limiting

`POST /auth/login` and `POST /auth/refresh` are limited per client IP (`AUTH_RATE_LIMIT_PER_MINUTE`, default 30). Excess requests return `429 Too Many Requests`.
