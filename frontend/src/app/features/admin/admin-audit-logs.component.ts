import { Component, inject, signal } from '@angular/core';
import { MatTableModule } from '@angular/material/table';

import { AuditLogEntry } from '../../core/models/audit.models';
import { AuditService } from '../../core/services/audit.service';

@Component({
  selector: 'app-admin-audit-logs',
  imports: [MatTableModule],
  template: `
    <h1>Audit log</h1>
    <table mat-table [dataSource]="rows()" class="mat-elevation-z1">
      <ng-container matColumnDef="when">
        <th mat-header-cell *matHeaderCellDef>When</th>
        <td mat-cell *matCellDef="let row">{{ row.created_at }}</td>
      </ng-container>
      <ng-container matColumnDef="action">
        <th mat-header-cell *matHeaderCellDef>Action</th>
        <td mat-cell *matCellDef="let row">{{ row.action }}</td>
      </ng-container>
      <ng-container matColumnDef="actor">
        <th mat-header-cell *matHeaderCellDef>Actor</th>
        <td mat-cell *matCellDef="let row">{{ row.actor_email ?? '—' }}</td>
      </ng-container>
      <ng-container matColumnDef="summary">
        <th mat-header-cell *matHeaderCellDef>Summary</th>
        <td mat-cell *matCellDef="let row">{{ row.summary }}</td>
      </ng-container>
      <tr mat-header-row *matHeaderRowDef="columns"></tr>
      <tr mat-row *matRowDef="let row; columns: columns"></tr>
    </table>
  `,
  styles: `
    table {
      width: 100%;
    }
  `,
})
export class AdminAuditLogsComponent {
  private readonly api = inject(AuditService);

  readonly rows = signal<AuditLogEntry[]>([]);
  readonly columns = ['when', 'action', 'actor', 'summary'];

  constructor() {
    this.api.list().subscribe({
      next: (page) => this.rows.set(page.items),
    });
  }
}
