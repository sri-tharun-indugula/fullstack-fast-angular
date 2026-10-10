import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { AttendanceDay, TeamAttendanceRow } from '../models/attendance.models';

@Injectable({ providedIn: 'root' })
export class AttendanceService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/attendance`;

  today(): Observable<AttendanceDay | null> {
    return this.http.get<AttendanceDay | null>(`${this.base}/today`);
  }

  checkIn(): Observable<AttendanceDay> {
    return this.http.post<AttendanceDay>(`${this.base}/check-in`, {});
  }

  checkOut(): Observable<AttendanceDay> {
    return this.http.post<AttendanceDay>(`${this.base}/check-out`, {});
  }

  myHistory(from?: string, to?: string): Observable<AttendanceDay[]> {
    let params = new HttpParams();
    if (from) {
      params = params.set('from', from);
    }
    if (to) {
      params = params.set('to', to);
    }
    return this.http.get<AttendanceDay[]>(`${this.base}/me`, { params });
  }

  team(date?: string): Observable<TeamAttendanceRow[]> {
    const params = date ? new HttpParams().set('date', date) : undefined;
    return this.http.get<TeamAttendanceRow[]>(`${this.base}/team`, { params });
  }
}
