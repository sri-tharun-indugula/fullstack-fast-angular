import { Component, inject, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';

import { DocumentScope, HrDocument } from '../../core/models/document.models';
import { EmployeeProfile } from '../../core/models/employee.models';
import { DocumentService } from '../../core/services/document.service';
import { EmployeeService } from '../../core/services/employee.service';

@Component({
  selector: 'app-admin-documents',
  imports: [MatFormFieldModule, MatInputModule, MatSelectModule, MatButtonModule],
  template: `
    <h1>Documents</h1>
    <section class="upload">
      <h2>Upload</h2>
      <mat-form-field appearance="outline" class="full">
        <mat-label>Title</mat-label>
        <input matInput #titleInput />
      </mat-form-field>
      <mat-form-field appearance="outline" class="full">
        <mat-label>Scope</mat-label>
        <mat-select [value]="scope()" (selectionChange)="scope.set($event.value)">
          <mat-option value="company">Company (all employees)</mat-option>
          <mat-option value="employee">Specific employee</mat-option>
        </mat-select>
      </mat-form-field>
      @if (scope() === 'employee') {
        <mat-form-field appearance="outline" class="full">
          <mat-label>Employee</mat-label>
          <mat-select [value]="ownerId()" (selectionChange)="ownerId.set($event.value)">
            @for (emp of employees(); track emp.user_id) {
              <mat-option [value]="emp.user_id">{{ emp.full_name }} ({{ emp.employee_code }})</mat-option>
            }
          </mat-select>
        </mat-form-field>
      }
      <input type="file" accept=".pdf,.txt,.png,.jpg,.jpeg" (change)="onFile($event)" />
      <button mat-flat-button type="button" (click)="upload(titleInput.value)" [disabled]="!selectedFile">
        Upload
      </button>
    </section>
    @for (doc of documents(); track doc.id) {
      <article class="doc">
        <h2>{{ doc.title }}</h2>
        <p class="meta">{{ doc.scope }} · {{ doc.original_filename }}</p>
        <button mat-button type="button" (click)="download(doc)">Download</button>
        <button mat-button type="button" color="warn" (click)="remove(doc)">Delete</button>
      </article>
    }
  `,
  styles: `
    .upload {
      margin-bottom: 1.5rem;
      padding: 1rem;
      border: 1px dashed var(--mat-sys-outline);
    }
    .full {
      width: 100%;
      max-width: 24rem;
      display: block;
    }
    .doc {
      border: 1px solid var(--mat-sys-outline-variant);
      border-radius: 8px;
      padding: 1rem;
      margin-bottom: 1rem;
    }
    .meta {
      color: var(--mat-sys-on-surface-variant);
    }
  `,
})
export class AdminDocumentsComponent {
  private readonly documentsApi = inject(DocumentService);
  private readonly employeesApi = inject(EmployeeService);

  readonly documents = signal<HrDocument[]>([]);
  readonly employees = signal<EmployeeProfile[]>([]);
  readonly scope = signal<DocumentScope>('company');
  readonly ownerId = signal<string | null>(null);
  selectedFile: File | null = null;

  constructor() {
    this.documentsApi.mine().subscribe({ next: (list) => this.documents.set(list) });
    this.employeesApi.list().subscribe({ next: (list) => this.employees.set(list) });
  }

  onFile(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.selectedFile = input.files?.[0] ?? null;
  }

  upload(title: string): void {
    if (!this.selectedFile || !title.trim()) {
      return;
    }
    const scope = this.scope();
    const owner = scope === 'employee' ? this.ownerId() : undefined;
    if (scope === 'employee' && !owner) {
      return;
    }
    this.documentsApi
      .upload(this.selectedFile, { title: title.trim(), scope, owner_user_id: owner ?? undefined })
      .subscribe({
        next: () => {
          this.selectedFile = null;
          this.documentsApi.mine().subscribe({ next: (list) => this.documents.set(list) });
        },
      });
  }

  download(doc: HrDocument): void {
    this.documentsApi.download(doc.id).subscribe({
      next: (blob) => {
        const url = URL.createObjectURL(blob);
        const anchor = document.createElement('a');
        anchor.href = url;
        anchor.download = doc.original_filename;
        anchor.click();
        URL.revokeObjectURL(url);
      },
    });
  }

  remove(doc: HrDocument): void {
    this.documentsApi.remove(doc.id).subscribe({
      next: () => this.documents.update((rows) => rows.filter((row) => row.id !== doc.id)),
    });
  }
}
