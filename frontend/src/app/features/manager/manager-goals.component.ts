import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatTableModule } from '@angular/material/table';

import { EmployeeProfile } from '../../core/models/employee.models';
import { PerformanceGoal } from '../../core/models/goal.models';
import { EmployeeService } from '../../core/services/employee.service';
import { GoalService } from '../../core/services/goal.service';

@Component({
  selector: 'app-manager-goals',
  imports: [
    ReactiveFormsModule,
    MatTableModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatButtonModule,
  ],
  template: `
    <h1>Team goals</h1>
    <form [formGroup]="form" (ngSubmit)="create()" class="create">
      <h2>Assign goal</h2>
      <mat-form-field appearance="outline">
        <mat-label>Employee</mat-label>
        <mat-select formControlName="assignee_user_id">
          @for (member of team(); track member.user_id) {
            <mat-option [value]="member.user_id">{{ member.full_name }}</mat-option>
          }
        </mat-select>
      </mat-form-field>
      <mat-form-field appearance="outline">
        <mat-label>Title</mat-label>
        <input matInput formControlName="title" />
      </mat-form-field>
      <mat-form-field appearance="outline">
        <mat-label>Description</mat-label>
        <textarea matInput rows="3" formControlName="description"></textarea>
      </mat-form-field>
      <mat-form-field appearance="outline">
        <mat-label>Due date</mat-label>
        <input matInput type="date" formControlName="due_date" />
      </mat-form-field>
      <button mat-flat-button color="primary" type="submit" [disabled]="form.invalid || saving()">Assign</button>
    </form>

    <table mat-table [dataSource]="goals()" class="mat-elevation-z1">
      <ng-container matColumnDef="employee">
        <th mat-header-cell *matHeaderCellDef>Employee</th>
        <td mat-cell *matCellDef="let row">{{ row.assignee_name }}</td>
      </ng-container>
      <ng-container matColumnDef="title">
        <th mat-header-cell *matHeaderCellDef>Goal</th>
        <td mat-cell *matCellDef="let row">{{ row.title }}</td>
      </ng-container>
      <ng-container matColumnDef="progress">
        <th mat-header-cell *matHeaderCellDef>Progress</th>
        <td mat-cell *matCellDef="let row">{{ row.progress_percent }}% · {{ row.status }}</td>
      </ng-container>
      <tr mat-header-row *matHeaderRowDef="columns"></tr>
      <tr mat-row *matRowDef="let row; columns: columns"></tr>
    </table>
  `,
  styles: `
    .create {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
      max-width: 28rem;
      margin-bottom: 1.5rem;
    }
    mat-form-field {
      width: 100%;
    }
    table {
      width: 100%;
    }
  `,
})
export class ManagerGoalsComponent {
  private readonly goalsApi = inject(GoalService);
  private readonly employeesApi = inject(EmployeeService);
  private readonly formBuilder = inject(FormBuilder);

  readonly team = signal<EmployeeProfile[]>([]);
  readonly goals = signal<PerformanceGoal[]>([]);
  readonly saving = signal(false);
  readonly columns = ['employee', 'title', 'progress'];

  readonly form = this.formBuilder.nonNullable.group({
    assignee_user_id: ['', Validators.required],
    title: ['', Validators.required],
    description: ['', Validators.required],
    due_date: [''],
  });

  constructor() {
    this.employeesApi.list().subscribe({ next: (items) => this.team.set(items) });
    this.reloadGoals();
  }

  reloadGoals(): void {
    this.goalsApi.team().subscribe({ next: (items) => this.goals.set(items) });
  }

  create(): void {
    if (this.form.invalid) {
      return;
    }
    this.saving.set(true);
    const raw = this.form.getRawValue();
    this.goalsApi
      .create({
        assignee_user_id: raw.assignee_user_id,
        title: raw.title,
        description: raw.description,
        due_date: raw.due_date || null,
      })
      .subscribe({
        next: () => {
          this.saving.set(false);
          this.form.reset();
          this.reloadGoals();
        },
        error: () => this.saving.set(false),
      });
  }
}
