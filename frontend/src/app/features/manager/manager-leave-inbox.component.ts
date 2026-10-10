import { Component, inject, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatTableModule } from '@angular/material/table';

import { LeaveRequest } from '../../core/models/leave.models';
import { LeaveService } from '../../core/services/leave.service';

@Component({
  selector: 'app-manager-leave-inbox',
  imports: [MatTableModule, MatButtonModule],
  template: `
    <h1>Leave inbox</h1>
    @if (inbox().length === 0) {
      <p>No pending leave requests.</p>
    } @else {
      <table mat-table [dataSource]="inbox()" class="mat-elevation-z1">
        <ng-container matColumnDef="employee">
          <th mat-header-cell *matHeaderCellDef>Employee</th>
          <td mat-cell *matCellDef="let row">{{ row.employee_name }}</td>
        </ng-container>
        <ng-container matColumnDef="type">
          <th mat-header-cell *matHeaderCellDef>Type</th>
          <td mat-cell *matCellDef="let row">{{ row.leave_type.name }}</td>
        </ng-container>
        <ng-container matColumnDef="dates">
          <th mat-header-cell *matHeaderCellDef>Dates</th>
          <td mat-cell *matCellDef="let row">{{ row.start_date }} → {{ row.end_date }} ({{ row.days }}d)</td>
        </ng-container>
        <ng-container matColumnDef="reason">
          <th mat-header-cell *matHeaderCellDef>Reason</th>
          <td mat-cell *matCellDef="let row">{{ row.reason }}</td>
        </ng-container>
        <ng-container matColumnDef="actions">
          <th mat-header-cell *matHeaderCellDef></th>
          <td mat-cell *matCellDef="let row">
            <button mat-button type="button" (click)="approve(row)">Approve</button>
            <button mat-button type="button" (click)="reject(row)">Reject</button>
          </td>
        </ng-container>
        <tr mat-header-row *matHeaderRowDef="columns"></tr>
        <tr mat-row *matRowDef="let row; columns: columns"></tr>
      </table>
    }
  `,
  styles: `
    table {
      width: 100%;
    }
  `,
})
export class ManagerLeaveInboxComponent {
  private readonly leaveApi = inject(LeaveService);

  readonly inbox = signal<LeaveRequest[]>([]);
  readonly columns = ['employee', 'type', 'dates', 'reason', 'actions'];

  constructor() {
    this.reload();
  }

  reload(): void {
    this.leaveApi.inbox().subscribe({ next: (items) => this.inbox.set(items) });
  }

  approve(row: LeaveRequest): void {
    this.leaveApi.approve(row.id).subscribe({ next: () => this.reload() });
  }

  reject(row: LeaveRequest): void {
    this.leaveApi.reject(row.id).subscribe({ next: () => this.reload() });
  }
}
