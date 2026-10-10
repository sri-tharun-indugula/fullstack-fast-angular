import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';

@Component({
  selector: 'app-manager-shell',
  imports: [RouterOutlet, RouterLink, RouterLinkActive, MatButtonModule],
  template: `
    <nav class="subnav">
      <a mat-button routerLink="/manager/team" routerLinkActive="active">Team</a>
      <a mat-button routerLink="/manager/leave" routerLinkActive="active">Leave inbox</a>
      <a mat-button routerLink="/manager/attendance" routerLinkActive="active">Attendance</a>
      <a mat-button routerLink="/manager/goals" routerLinkActive="active">Goals</a>
      <a mat-button routerLink="/manager/documents" routerLinkActive="active">Documents</a>
      <a mat-button routerLink="/manager/reports" routerLinkActive="active">Reports</a>
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
export class ManagerShellComponent {}
