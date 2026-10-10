import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { AuditLogList } from '../models/audit.models';

@Injectable({ providedIn: 'root' })
export class AuditService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/admin/audit-logs`;

  list(limit = 50, offset = 0): Observable<AuditLogList> {
    return this.http.get<AuditLogList>(`${this.base}?limit=${limit}&offset=${offset}`);
  }
}
