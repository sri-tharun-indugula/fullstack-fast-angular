import { Component, inject, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatTableModule } from '@angular/material/table';

import { AttendanceDay } from '../../core/models/attendance.models';
import { AttendanceService } from '../../core/services/attendance.service';

@Component({
  selector: 'app-employee-attendance',
  imports: [MatTableModule, MatButtonModule],
  template: `
    <h1>Attendance</h1>
    <section class="today">
      <h2>Today</h2>
      @if (today(); as record) {
        <p>Checked in: {{ formatTime(record.check_in_at) }}</p>
        @if (record.check_out_at) {
          <p>Checked out: {{ formatTime(record.check_out_at) }}</p>
        } @else {
          <button mat-flat-button color="primary" type="button" (click)="checkOut()" [disabled]="busy()">
            Check out
          </button>
        }
      } @else {
        <p>You have not checked in yet.</p>
        <button mat-flat-button color="primary" type="button" (click)="checkIn()" [disabled]="busy()">
          Check in
        </button>
      }
      @if (errorMessage(); as message) {
        <p class="error">{{ message }}</p>
      }
    </section>

    <h2>Recent history</h2>
    <table mat-table [dataSource]="history()" class="mat-elevation-z1">
      <ng-container matColumnDef="date">
        <th mat-header-cell *matHeaderCellDef>Date</th>
        <td mat-cell *matCellDef="let row">{{ row.work_date }}</td>
      </ng-container>
      <ng-container matColumnDef="in">
        <th mat-header-cell *matHeaderCellDef>Check in</th>
        <td mat-cell *matCellDef="let row">{{ formatTime(row.check_in_at) }}</td>
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
    .today {
      margin-bottom: 1.5rem;
    }
    table {
      width: 100%;
    }
    .error {
      color: var(--mat-sys-error);
    }
  `,
})
export class EmployeeAttendanceComponent {
  private readonly attendanceApi = inject(AttendanceService);

  readonly today = signal<AttendanceDay | null>(null);
  readonly history = signal<AttendanceDay[]>([]);
  readonly busy = signal(false);
  readonly errorMessage = signal<string | null>(null);
  readonly columns = ['date', 'in', 'out'];

  constructor() {
    this.reload();
  }

  reload(): void {
    this.attendanceApi.today().subscribe({ next: (record) => this.today.set(record) });
    this.attendanceApi.myHistory().subscribe({ next: (items) => this.history.set(items) });
  }

  checkIn(): void {
    this.run(() => this.attendanceApi.checkIn());
  }

  checkOut(): void {
    this.run(() => this.attendanceApi.checkOut());
  }

  private run(action: () => ReturnType<AttendanceService['checkIn']>): void {
    this.busy.set(true);
    this.errorMessage.set(null);
    action().subscribe({
      next: () => {
        this.busy.set(false);
        this.reload();
      },
      error: (err) => {
        this.busy.set(false);
        const detail = err.error?.detail;
        this.errorMessage.set(typeof detail === 'string' ? detail : 'Action failed');
      },
    });
  }

  formatTime(iso: string): string {
    return new Date(iso).toLocaleString();
  }
}
