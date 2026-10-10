import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { LeaveBalance, LeaveRequest, LeaveRequestCreate, LeaveType } from '../models/leave.models';

@Injectable({ providedIn: 'root' })
export class LeaveService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/leave`;

  types(): Observable<LeaveType[]> {
    return this.http.get<LeaveType[]>(`${this.base}/types`);
  }

  myBalances(): Observable<LeaveBalance[]> {
    return this.http.get<LeaveBalance[]>(`${this.base}/balances/me`);
  }

  myRequests(): Observable<LeaveRequest[]> {
    return this.http.get<LeaveRequest[]>(`${this.base}/requests/me`);
  }

  apply(body: LeaveRequestCreate): Observable<LeaveRequest> {
    return this.http.post<LeaveRequest>(`${this.base}/requests`, body);
  }

  cancel(requestId: string): Observable<LeaveRequest> {
    return this.http.post<LeaveRequest>(`${this.base}/requests/${requestId}/cancel`, {});
  }

  inbox(): Observable<LeaveRequest[]> {
    return this.http.get<LeaveRequest[]>(`${this.base}/requests/inbox`);
  }

  approve(requestId: string, note?: string): Observable<LeaveRequest> {
    return this.http.post<LeaveRequest>(`${this.base}/requests/${requestId}/approve`, { note: note ?? null });
  }

  reject(requestId: string, note?: string): Observable<LeaveRequest> {
    return this.http.post<LeaveRequest>(`${this.base}/requests/${requestId}/reject`, { note: note ?? null });
  }
}
