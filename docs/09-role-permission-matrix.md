# Role permission matrix

Roles are stored on `users.role`. The API enforces them. The Angular `roleGuard` only chooses which shell to show.

| Capability | Admin | Manager | Employee |
| --- | --- | --- | --- |
| `POST /auth/login`, `/auth/refresh`, `/auth/logout` | yes | yes | yes |
| `GET /auth/me` | yes | yes | yes |
| `GET /admin/ping` | yes | no | no |
| `GET /departments` | yes | yes | no |
| `POST /departments`, `PATCH /departments/{id}` | yes | no | no |
| `GET /employees/me`, `PATCH /employees/me` | yes* | yes* | yes* |
| `GET /employees` (list) | all | direct reports | no |
| `GET /employees/{user_id}` | any | direct report | self only |
| `POST /employees`, `PATCH /employees/{user_id}` | yes | no | no |
| `GET /leave/types`, `/leave/balances/me`, `/leave/requests/me` | yes* | yes* | yes* |
| `POST /leave/requests`, `/leave/requests/{id}/cancel` | yes* | yes* | yes* |
| `GET /leave/requests/inbox` | all pending | direct reports pending | no |
| `POST /leave/requests/{id}/approve`, `/reject` | any pending | direct reports pending | no |
| `GET /attendance/today`, check-in, check-out, `/attendance/me` | yes* | yes* | yes* |
| `GET /attendance/team` | all employees | direct reports | no |
| `GET /goals/me`, `PATCH /goals/{id}/self` | yes* | yes* | yes* |
| `GET /goals/team`, `POST /goals`, `PATCH /goals/{id}` | all | direct reports | no |
| `GET /documents/me`, download, upload, delete | company + all employee docs; upload company | company + team/self docs; upload for reports/self | company + self docs; upload self |
| `GET /notifications/me`, unread count, mark read | yes | yes | yes |
| `GET /admin/audit-logs` | yes | no | no |
| `GET /reports/overview` | yes | no | no |
| `GET /reports/team` | all employees | direct reports | no |
| Open `/admin` shell | yes | no | no |
| Open `/manager` shell | yes | yes | no |
| Open `/employee` shell | yes | no | yes |

\* Requires an `employee_profiles` row. Seed creates profiles for the three demo users.

After login, the client sends admin to `/admin`, manager to `/manager`, and employee to `/employee`.

Inactive users cannot obtain or use tokens.

Future modules must add rows here before their routes are merged.
