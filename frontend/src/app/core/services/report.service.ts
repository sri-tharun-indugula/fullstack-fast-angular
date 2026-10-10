import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { ReportsOverview, TeamReportsOverview } from '../models/report.models';

@Injectable({ providedIn: 'root' })
export class ReportService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/reports`;

  overview(): Observable<ReportsOverview> {
    return this.http.get<ReportsOverview>(`${this.base}/overview`);
  }

  team(): Observable<TeamReportsOverview> {
    return this.http.get<TeamReportsOverview>(`${this.base}/team`);
  }
}
