import { Component, inject, signal } from '@angular/core';

import { TeamReportsOverview } from '../../core/models/report.models';
import { ReportService } from '../../core/services/report.service';

@Component({
  selector: 'app-manager-reports',
  template: `
    <h1>Team snapshot</h1>
    @if (team(); as data) {
      <div class="cards">
        <div class="card">Direct reports: {{ data.direct_reports }}</div>
        <div class="card">Pending leave: {{ data.pending_leave_requests }}</div>
        <div class="card">Checked in today (UTC): {{ data.checked_in_today }}</div>
      </div>
    }
  `,
  styles: `
    .cards {
      display: flex;
      flex-wrap: wrap;
      gap: 1rem;
    }
    .card {
      padding: 1rem 1.25rem;
      border-radius: 8px;
      border: 1px solid var(--mat-sys-outline-variant);
    }
  `,
})
export class ManagerReportsComponent {
  private readonly api = inject(ReportService);

  readonly team = signal<TeamReportsOverview | null>(null);

  constructor() {
    this.api.team().subscribe({
      next: (data) => this.team.set(data),
    });
  }
}
