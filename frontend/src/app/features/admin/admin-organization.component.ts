import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatTableModule } from '@angular/material/table';

import { Department } from '../../core/models/employee.models';
import { DepartmentService } from '../../core/services/department.service';

@Component({
  selector: 'app-admin-organization',
  imports: [
    ReactiveFormsModule,
    MatTableModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
  ],
  template: `
    <h1>Organization</h1>
    <table mat-table [dataSource]="departments()" class="mat-elevation-z1">
      <ng-container matColumnDef="code">
        <th mat-header-cell *matHeaderCellDef>Code</th>
        <td mat-cell *matCellDef="let row">{{ row.code }}</td>
      </ng-container>
      <ng-container matColumnDef="name">
        <th mat-header-cell *matHeaderCellDef>Name</th>
        <td mat-cell *matCellDef="let row">{{ row.name }}</td>
      </ng-container>
      <tr mat-header-row *matHeaderRowDef="displayedColumns"></tr>
      <tr mat-row *matRowDef="let row; columns: displayedColumns"></tr>
    </table>

    <form [formGroup]="form" (ngSubmit)="create()" class="create">
      <h2>Add department</h2>
      <mat-form-field appearance="outline">
        <mat-label>Code</mat-label>
        <input matInput formControlName="code" placeholder="ENG" />
      </mat-form-field>
      <mat-form-field appearance="outline">
        <mat-label>Name</mat-label>
        <input matInput formControlName="name" />
      </mat-form-field>
      @if (errorMessage(); as message) {
        <p class="error">{{ message }}</p>
      }
      <button mat-flat-button color="primary" type="submit" [disabled]="form.invalid || saving()">Create</button>
    </form>
  `,
  styles: `
    table {
      width: 100%;
      margin-bottom: 1.5rem;
    }
    .create {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
      max-width: 24rem;
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
export class AdminOrganizationComponent {
  private readonly departmentsApi = inject(DepartmentService);
  private readonly formBuilder = inject(FormBuilder);

  readonly departments = signal<Department[]>([]);
  readonly saving = signal(false);
  readonly errorMessage = signal<string | null>(null);
  readonly displayedColumns = ['code', 'name'];

  readonly form = this.formBuilder.nonNullable.group({
    code: ['', [Validators.required, Validators.pattern(/^[A-Za-z0-9_-]+$/)]],
    name: ['', Validators.required],
  });

  constructor() {
    this.reload();
  }

  reload(): void {
    this.departmentsApi.list().subscribe({
      next: (items) => this.departments.set(items),
    });
  }

  create(): void {
    if (this.form.invalid) {
      return;
    }
    this.saving.set(true);
    this.errorMessage.set(null);
    const { code, name } = this.form.getRawValue();
    this.departmentsApi.create({ code: code.toUpperCase(), name }).subscribe({
      next: () => {
        this.saving.set(false);
        this.form.reset();
        this.reload();
      },
      error: () => {
        this.saving.set(false);
        this.errorMessage.set('Could not create department');
      },
    });
  }
}
