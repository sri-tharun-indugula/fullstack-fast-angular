import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatTableModule } from '@angular/material/table';

import { TeamAttendanceRow } from '../../core/models/attendance.models';
import { AttendanceService } from '../../core/services/attendance.service';

@Component({
  selector: 'app-manager-attendance',
  imports: [ReactiveFormsModule, MatTableModule, MatFormFieldModule, MatInputModule, MatButtonModule],
  template: `
    <h1>Team attendance</h1>
    <form [formGroup]="form" (ngSubmit)="load()" class="filter">
      <mat-form-field appearance="outline">
        <mat-label>Date</mat-label>
        <input matInput type="date" formControlName="work_date" />
      </mat-form-field>
      <button mat-flat-button color="primary" type="submit">Load</button>
    </form>
    <table mat-table [dataSource]="rows()" class="mat-elevation-z1">
      <ng-container matColumnDef="employee">
        <th mat-header-cell *matHeaderCellDef>Employee</th>
        <td mat-cell *matCellDef="let row">{{ row.full_name }} ({{ row.employee_code ?? '—' }})</td>
      </ng-container>
      <ng-container matColumnDef="in">
        <th mat-header-cell *matHeaderCellDef>Check in</th>
        <td mat-cell *matCellDef="let row">{{ row.check_in_at ? formatTime(row.check_in_at) : '—' }}</td>
      </ng-container>
      <ng-container matColumnDef="out">
        <th mat-header-cell *matHeaderCellDef>Check out</th>
        <td mat-cell *matCellDef="let row">{{ row.check_out_at ? formatTime(row.check_out_at) : '—' }}</td>
      </ng-container>
      <tr mat-header-row *matHeaderRowDef="columns"></tr>
      <tr mat-row *matRowDef="let row; columns: columns"></tr>
    </table>
  `,
  styles: `
    .filter {
      display: flex;
      gap: 1rem;
      align-items: center;
      margin-bottom: 1rem;
    }
    table {
      width: 100%;
    }
  `,
})
export class ManagerAttendanceComponent {
  private readonly attendanceApi = inject(AttendanceService);
  private readonly formBuilder = inject(FormBuilder);

  readonly rows = signal<TeamAttendanceRow[]>([]);
  readonly columns = ['employee', 'in', 'out'];

  readonly form = this.formBuilder.nonNullable.group({
    work_date: [new Date().toISOString().slice(0, 10)],
  });

  constructor() {
    this.load();
  }

  load(): void {
    const { work_date } = this.form.getRawValue();
    this.attendanceApi.team(work_date).subscribe({ next: (items) => this.rows.set(items) });
  }

  formatTime(iso: string): string {
    return new Date(iso).toLocaleString();
  }
}
