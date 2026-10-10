import { Component, inject, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';

import { HrDocument } from '../../core/models/document.models';
import { DocumentService } from '../../core/services/document.service';

@Component({
  selector: 'app-employee-documents',
  imports: [MatFormFieldModule, MatInputModule, MatButtonModule],
  template: `
    <h1>Documents</h1>
    <section class="upload">
      <h2>Upload personal document</h2>
      <mat-form-field appearance="outline" class="full">
        <mat-label>Title</mat-label>
        <input matInput #titleInput />
      </mat-form-field>
      <input type="file" accept=".pdf,.txt,.png,.jpg,.jpeg" (change)="onFile($event)" />
      <button mat-flat-button type="button" (click)="upload(titleInput.value)" [disabled]="!selectedFile">
        Upload
      </button>
    </section>
    @if (documents().length === 0) {
      <p>No documents yet.</p>
    }
    @for (doc of documents(); track doc.id) {
      <article class="doc">
        <h2>{{ doc.title }}</h2>
        <p>{{ doc.description ?? '—' }}</p>
        <p class="meta">
          {{ doc.scope }} · {{ doc.original_filename }} · {{ doc.uploaded_by_name }}
        </p>
        <button mat-button type="button" (click)="download(doc)">Download</button>
      </article>
    }
  `,
  styles: `
    .upload {
      margin-bottom: 1.5rem;
      padding: 1rem;
      border-radius: 8px;
      border: 1px dashed var(--mat-sys-outline);
    }
    .full {
      width: 100%;
      max-width: 24rem;
    }
    .doc {
      border: 1px solid var(--mat-sys-outline-variant);
      border-radius: 8px;
      padding: 1rem;
      margin-bottom: 1rem;
    }
    .meta {
      color: var(--mat-sys-on-surface-variant);
      font-size: 0.875rem;
    }
  `,
})
export class EmployeeDocumentsComponent {
  private readonly api = inject(DocumentService);

  readonly documents = signal<HrDocument[]>([]);
  selectedFile: File | null = null;

  constructor() {
    this.reload();
  }

  reload(): void {
    this.api.mine().subscribe({
      next: (list) => this.documents.set(list),
    });
  }

  onFile(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.selectedFile = input.files?.[0] ?? null;
  }

  upload(title: string): void {
    if (!this.selectedFile || !title.trim()) {
      return;
    }
    this.api
      .upload(this.selectedFile, { title: title.trim(), scope: 'employee' })
      .subscribe({
        next: () => {
          this.selectedFile = null;
          this.reload();
        },
      });
  }

  download(doc: HrDocument): void {
    this.api.download(doc.id).subscribe({
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
}
