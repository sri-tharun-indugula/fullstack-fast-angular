import { Component, inject, signal } from '@angular/core';
import { MatTableModule } from '@angular/material/table';

import { EmployeeProfile } from '../../core/models/employee.models';
import { EmployeeService } from '../../core/services/employee.service';

@Component({
  selector: 'app-manager-team',
  imports: [MatTableModule],
  template: `
    <h1>My team</h1>
    @if (employees().length === 0) {
      <p>No direct reports yet.</p>
    } @else {
      <table mat-table [dataSource]="employees()" class="mat-elevation-z1">
        <ng-container matColumnDef="name">
          <th mat-header-cell *matHeaderCellDef>Name</th>
          <td mat-cell *matCellDef="let row">{{ row.full_name }}</td>
        </ng-container>
        <ng-container matColumnDef="title">
          <th mat-header-cell *matHeaderCellDef>Title</th>
          <td mat-cell *matCellDef="let row">{{ row.job_title }}</td>
        </ng-container>
        <ng-container matColumnDef="department">
          <th mat-header-cell *matHeaderCellDef>Department</th>
          <td mat-cell *matCellDef="let row">{{ row.department?.name ?? '—' }}</td>
        </ng-container>
        <tr mat-header-row *matHeaderRowDef="displayedColumns"></tr>
        <tr mat-row *matRowDef="let row; columns: displayedColumns"></tr>
      </table>
    }
  `,
  styles: `
    table {
      width: 100%;
    }
  `,
})
export class ManagerTeamComponent {
  private readonly employeesApi = inject(EmployeeService);

  readonly employees = signal<EmployeeProfile[]>([]);
  readonly displayedColumns = ['name', 'title', 'department'];

  constructor() {
    this.employeesApi.list().subscribe({
      next: (items) => this.employees.set(items),
    });
  }
}
