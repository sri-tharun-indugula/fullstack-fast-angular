import { Routes } from '@angular/router';

import { authGuard, guestGuard, homeRedirectGuard, roleGuard } from './core/auth/auth.guards';

export const routes: Routes = [
  {
    path: 'login',
    canActivate: [guestGuard],
    loadComponent: () => import('./features/auth/login.component').then((m) => m.LoginComponent),
  },
  {
    path: '',
    canActivate: [authGuard],
    loadComponent: () => import('./shared/layout/shell.component').then((m) => m.ShellComponent),
    children: [
      { path: '', pathMatch: 'full', canActivate: [homeRedirectGuard], children: [] },
      {
        path: 'notifications',
        loadComponent: () =>
          import('./features/shared/notifications.component').then((m) => m.NotificationsComponent),
      },
      {
        path: 'admin',
        canActivate: [roleGuard],
        data: { roles: ['admin'] },
        loadComponent: () => import('./features/admin/admin-shell.component').then((m) => m.AdminShellComponent),
        children: [
          { path: '', pathMatch: 'full', redirectTo: 'organization' },
          {
            path: 'organization',
            loadComponent: () =>
              import('./features/admin/admin-organization.component').then((m) => m.AdminOrganizationComponent),
          },
          {
            path: 'employees',
            loadComponent: () =>
              import('./features/admin/admin-employees.component').then((m) => m.AdminEmployeesComponent),
          },
          {
            path: 'documents',
            loadComponent: () =>
              import('./features/admin/admin-documents.component').then((m) => m.AdminDocumentsComponent),
          },
          {
            path: 'reports',
            loadComponent: () =>
              import('./features/admin/admin-reports.component').then((m) => m.AdminReportsComponent),
          },
          {
            path: 'audit',
            loadComponent: () =>
              import('./features/admin/admin-audit-logs.component').then((m) => m.AdminAuditLogsComponent),
          },
        ],
      },
      {
        path: 'manager',
        canActivate: [roleGuard],
        data: { roles: ['admin', 'manager'] },
        loadComponent: () => import('./features/manager/manager-shell.component').then((m) => m.ManagerShellComponent),
        children: [
          { path: '', pathMatch: 'full', redirectTo: 'team' },
          {
            path: 'team',
            loadComponent: () => import('./features/manager/manager-team.component').then((m) => m.ManagerTeamComponent),
          },
          {
            path: 'leave',
            loadComponent: () =>
              import('./features/manager/manager-leave-inbox.component').then((m) => m.ManagerLeaveInboxComponent),
          },
          {
            path: 'attendance',
            loadComponent: () =>
              import('./features/manager/manager-attendance.component').then((m) => m.ManagerAttendanceComponent),
          },
          {
            path: 'goals',
            loadComponent: () => import('./features/manager/manager-goals.component').then((m) => m.ManagerGoalsComponent),
          },
          {
            path: 'documents',
            loadComponent: () =>
              import('./features/employee/employee-documents.component').then((m) => m.EmployeeDocumentsComponent),
          },
          {
            path: 'reports',
            loadComponent: () =>
              import('./features/manager/manager-reports.component').then((m) => m.ManagerReportsComponent),
          },
        ],
      },
      {
        path: 'employee',
        canActivate: [roleGuard],
        data: { roles: ['admin', 'employee'] },
        loadComponent: () => import('./features/employee/employee-shell.component').then((m) => m.EmployeeShellComponent),
        children: [
          { path: '', pathMatch: 'full', redirectTo: 'profile' },
          {
            path: 'profile',
            loadComponent: () =>
              import('./features/employee/employee-profile.component').then((m) => m.EmployeeProfileComponent),
          },
          {
            path: 'leave',
            loadComponent: () =>
              import('./features/employee/employee-leave.component').then((m) => m.EmployeeLeaveComponent),
          },
          {
            path: 'attendance',
            loadComponent: () =>
              import('./features/employee/employee-attendance.component').then((m) => m.EmployeeAttendanceComponent),
          },
          {
            path: 'goals',
            loadComponent: () => import('./features/employee/employee-goals.component').then((m) => m.EmployeeGoalsComponent),
          },
          {
            path: 'documents',
            loadComponent: () =>
              import('./features/employee/employee-documents.component').then((m) => m.EmployeeDocumentsComponent),
          },
        ],
      },
    ],
  },
  { path: '**', redirectTo: 'login' },
];
