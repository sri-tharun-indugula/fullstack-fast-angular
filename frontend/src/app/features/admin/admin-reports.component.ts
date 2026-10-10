import { Component, inject, signal } from '@angular/core';
import { MatTableModule } from '@angular/material/table';

import { ReportsOverview } from '../../core/models/report.models';
import { ReportService } from '../../core/services/report.service';

@Component({
  selector: 'app-admin-reports',
  imports: [MatTableModule],
  template: `
    <h1>Reports</h1>
    @if (overview(); as data) {
      <section class="cards">
        <div class="card">Employees: {{ data.total_employees }}</div>
        <div class="card">Pending leave: {{ data.pending_leave_requests }}</div>
        <div class="card">Checked in today (UTC): {{ data.checked_in_today }}</div>
      </section>
      <h2>Headcount by department</h2>
      <table mat-table [dataSource]="data.headcount_by_department" class="mat-elevation-z1">
        <ng-container matColumnDef="department">
          <th mat-header-cell *matHeaderCellDef>Department</th>
          <td mat-cell *matCellDef="let row">{{ row.department_name }}</td>
        </ng-container>
        <ng-container matColumnDef="count">
          <th mat-header-cell *matHeaderCellDef>Employees</th>
          <td mat-cell *matCellDef="let row">{{ row.employee_count }}</td>
        </ng-container>
        <tr mat-header-row *matHeaderRowDef="columns"></tr>
        <tr mat-row *matRowDef="let row; columns: columns"></tr>
      </table>
    }
  `,
  styles: `
    .cards {
      display: flex;
      flex-wrap: wrap;
      gap: 1rem;
      margin-bottom: 1.5rem;
    }
    .card {
      padding: 1rem 1.25rem;
      border-radius: 8px;
      border: 1px solid var(--mat-sys-outline-variant);
    }
    table {
      width: 100%;
      max-width: 32rem;
    }
  `,
})
export class AdminReportsComponent {
  private readonly api = inject(ReportService);

  readonly overview = signal<ReportsOverview | null>(null);
  readonly columns = ['department', 'count'];

  constructor() {
    this.api.overview().subscribe({
      next: (data) => this.overview.set(data),
    });
  }
}
