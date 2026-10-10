import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatTableModule } from '@angular/material/table';

import { LeaveBalance, LeaveRequest, LeaveType } from '../../core/models/leave.models';
import { LeaveService } from '../../core/services/leave.service';

@Component({
  selector: 'app-employee-leave',
  imports: [
    ReactiveFormsModule,
    MatTableModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatButtonModule,
  ],
  template: `
    <h1>Leave</h1>
    <h2>Balances</h2>
    <table mat-table [dataSource]="balances()" class="mat-elevation-z1">
      <ng-container matColumnDef="type">
        <th mat-header-cell *matHeaderCellDef>Type</th>
        <td mat-cell *matCellDef="let row">{{ row.leave_type.name }}</td>
      </ng-container>
      <ng-container matColumnDef="available">
        <th mat-header-cell *matHeaderCellDef>Available</th>
        <td mat-cell *matCellDef="let row">{{ row.available }} / {{ row.entitled }}</td>
      </ng-container>
      <ng-container matColumnDef="pending">
        <th mat-header-cell *matHeaderCellDef>Pending</th>
        <td mat-cell *matCellDef="let row">{{ row.pending }}</td>
      </ng-container>
      <tr mat-header-row *matHeaderRowDef="balanceColumns"></tr>
      <tr mat-row *matRowDef="let row; columns: balanceColumns"></tr>
    </table>

    <form [formGroup]="form" (ngSubmit)="apply()" class="apply">
      <h2>Apply for leave</h2>
      <mat-form-field appearance="outline">
        <mat-label>Leave type</mat-label>
        <mat-select formControlName="leave_type_id">
          @for (type of types(); track type.id) {
            <mat-option [value]="type.id">{{ type.name }}</mat-option>
          }
        </mat-select>
      </mat-form-field>
      <mat-form-field appearance="outline">
        <mat-label>Start date</mat-label>
        <input matInput type="date" formControlName="start_date" />
      </mat-form-field>
      <mat-form-field appearance="outline">
        <mat-label>End date</mat-label>
        <input matInput type="date" formControlName="end_date" />
      </mat-form-field>
      <mat-form-field appearance="outline">
        <mat-label>Reason</mat-label>
        <textarea matInput rows="3" formControlName="reason"></textarea>
      </mat-form-field>
      @if (errorMessage(); as message) {
        <p class="error">{{ message }}</p>
      }
      <button mat-flat-button color="primary" type="submit" [disabled]="form.invalid || submitting()">Submit</button>
    </form>

    <h2>My requests</h2>
    <table mat-table [dataSource]="requests()" class="mat-elevation-z1">
      <ng-container matColumnDef="type">
        <th mat-header-cell *matHeaderCellDef>Type</th>
        <td mat-cell *matCellDef="let row">{{ row.leave_type.code }}</td>
      </ng-container>
      <ng-container matColumnDef="dates">
        <th mat-header-cell *matHeaderCellDef>Dates</th>
        <td mat-cell *matCellDef="let row">{{ row.start_date }} → {{ row.end_date }}</td>
      </ng-container>
      <ng-container matColumnDef="days">
        <th mat-header-cell *matHeaderCellDef>Days</th>
        <td mat-cell *matCellDef="let row">{{ row.days }}</td>
      </ng-container>
      <ng-container matColumnDef="status">
        <th mat-header-cell *matHeaderCellDef>Status</th>
        <td mat-cell *matCellDef="let row">{{ row.status }}</td>
      </ng-container>
      <ng-container matColumnDef="actions">
        <th mat-header-cell *matHeaderCellDef></th>
        <td mat-cell *matCellDef="let row">
          @if (row.status === 'pending') {
            <button mat-button type="button" (click)="cancel(row)">Cancel</button>
          }
        </td>
      </ng-container>
      <tr mat-header-row *matHeaderRowDef="requestColumns"></tr>
      <tr mat-row *matRowDef="let row; columns: requestColumns"></tr>
    </table>
  `,
  styles: `
    table {
      width: 100%;
      margin-bottom: 1.5rem;
    }
    .apply {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
      max-width: 28rem;
      margin-bottom: 1.5rem;
    }
    mat-form-field {
      width: 100%;
    }
    .error {
      color: var(--mat-sys-error);
      margin: 0;
    }
  `,
})
export class EmployeeLeaveComponent {
  private readonly leaveApi = inject(LeaveService);
  private readonly formBuilder = inject(FormBuilder);

  readonly types = signal<LeaveType[]>([]);
  readonly balances = signal<LeaveBalance[]>([]);
  readonly requests = signal<LeaveRequest[]>([]);
  readonly submitting = signal(false);
  readonly errorMessage = signal<string | null>(null);
  readonly balanceColumns = ['type', 'available', 'pending'];
  readonly requestColumns = ['type', 'dates', 'days', 'status', 'actions'];

  readonly form = this.formBuilder.nonNullable.group({
    leave_type_id: ['', Validators.required],
    start_date: ['', Validators.required],
    end_date: ['', Validators.required],
    reason: ['', Validators.required],
  });

  constructor() {
    this.reload();
    this.leaveApi.types().subscribe({ next: (items) => this.types.set(items) });
  }

  reload(): void {
    this.leaveApi.myBalances().subscribe({ next: (items) => this.balances.set(items) });
    this.leaveApi.myRequests().subscribe({ next: (items) => this.requests.set(items) });
  }

  apply(): void {
    if (this.form.invalid) {
      return;
    }
    this.submitting.set(true);
    this.errorMessage.set(null);
    this.leaveApi.apply(this.form.getRawValue()).subscribe({
      next: () => {
        this.submitting.set(false);
        this.form.reset();
        this.reload();
      },
      error: (err) => {
        this.submitting.set(false);
        const detail = err.error?.detail;
        this.errorMessage.set(typeof detail === 'string' ? detail : 'Could not submit leave request');
      },
    });
  }

  cancel(row: LeaveRequest): void {
    this.leaveApi.cancel(row.id).subscribe({ next: () => this.reload() });
  }
}
