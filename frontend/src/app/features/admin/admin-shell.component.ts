import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';

@Component({
  selector: 'app-admin-shell',
  imports: [RouterOutlet, RouterLink, RouterLinkActive, MatButtonModule],
  template: `
    <nav class="subnav">
      <a mat-button routerLink="/admin/organization" routerLinkActive="active">Organization</a>
      <a mat-button routerLink="/admin/employees" routerLinkActive="active">Employees</a>
      <a mat-button routerLink="/admin/documents" routerLinkActive="active">Documents</a>
      <a mat-button routerLink="/admin/reports" routerLinkActive="active">Reports</a>
      <a mat-button routerLink="/admin/audit" routerLinkActive="active">Audit</a>
    </nav>
    <router-outlet />
  `,
  styles: `
    .subnav {
      display: flex;
      gap: 0.25rem;
      margin-bottom: 1rem;
    }
    a.active {
      font-weight: 600;
    }
  `,
})
export class AdminShellComponent {}
