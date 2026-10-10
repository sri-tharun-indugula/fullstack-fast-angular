import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';

import { EmployeeProfile } from '../../core/models/employee.models';
import { EmployeeService } from '../../core/services/employee.service';

@Component({
  selector: 'app-employee-profile',
  imports: [ReactiveFormsModule, MatFormFieldModule, MatInputModule, MatButtonModule],
  template: `
    <h1>My profile</h1>
    @if (profile(); as p) {
      <dl class="meta">
        <dt>Name</dt>
        <dd>{{ p.full_name }}</dd>
        <dt>Employee code</dt>
        <dd>{{ p.employee_code }}</dd>
        <dt>Job title</dt>
        <dd>{{ p.job_title }}</dd>
        <dt>Department</dt>
        <dd>{{ p.department?.name ?? '—' }}</dd>
        <dt>Manager</dt>
        <dd>{{ p.manager_full_name ?? '—' }}</dd>
      </dl>
      <form [formGroup]="form" (ngSubmit)="save()">
        <mat-form-field appearance="outline">
          <mat-label>Phone</mat-label>
          <input matInput formControlName="phone" />
        </mat-form-field>
        <mat-form-field appearance="outline">
          <mat-label>Work location</mat-label>
          <input matInput formControlName="work_location" />
        </mat-form-field>
        @if (message(); as text) {
          <p class="message">{{ text }}</p>
        }
        <button mat-flat-button color="primary" type="submit" [disabled]="saving()">Save</button>
      </form>
    }
  `,
  styles: `
    .meta {
      display: grid;
      grid-template-columns: 10rem 1fr;
      gap: 0.25rem 1rem;
      margin-bottom: 1.5rem;
    }
    dt {
      font-weight: 500;
      color: var(--mat-sys-on-surface-variant);
    }
    form {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
      max-width: 24rem;
    }
    mat-form-field {
      width: 100%;
    }
    .message {
      margin: 0;
    }
  `,
})
export class EmployeeProfileComponent {
  private readonly employeesApi = inject(EmployeeService);
  private readonly formBuilder = inject(FormBuilder);

  readonly profile = signal<EmployeeProfile | null>(null);
  readonly saving = signal(false);
  readonly message = signal<string | null>(null);

  readonly form = this.formBuilder.nonNullable.group({
    phone: [''],
    work_location: [''],
  });

  constructor() {
    this.employeesApi.me().subscribe({
      next: (profile) => {
        this.profile.set(profile);
        this.form.patchValue({
          phone: profile.phone ?? '',
          work_location: profile.work_location ?? '',
        });
      },
    });
  }

  save(): void {
    this.saving.set(true);
    this.message.set(null);
    const { phone, work_location } = this.form.getRawValue();
    this.employeesApi.updateMe({ phone, work_location }).subscribe({
      next: (profile) => {
        this.profile.set(profile);
        this.saving.set(false);
        this.message.set('Profile updated');
      },
      error: () => {
        this.saving.set(false);
        this.message.set('Update failed');
      },
    });
  }
}
