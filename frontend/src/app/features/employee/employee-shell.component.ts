import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';

@Component({
  selector: 'app-employee-shell',
  imports: [RouterOutlet, RouterLink, RouterLinkActive, MatButtonModule],
  template: `
    <nav class="subnav">
      <a mat-button routerLink="/employee/profile" routerLinkActive="active">Profile</a>
      <a mat-button routerLink="/employee/leave" routerLinkActive="active">Leave</a>
      <a mat-button routerLink="/employee/attendance" routerLinkActive="active">Attendance</a>
      <a mat-button routerLink="/employee/goals" routerLinkActive="active">Goals</a>
      <a mat-button routerLink="/employee/documents" routerLinkActive="active">Documents</a>
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
export class EmployeeShellComponent {}
