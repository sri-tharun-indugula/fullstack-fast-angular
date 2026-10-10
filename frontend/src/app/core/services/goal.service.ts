import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import {
  GoalCreate,
  GoalEmployeeUpdate,
  GoalManagerUpdate,
  PerformanceGoal,
} from '../models/goal.models';

@Injectable({ providedIn: 'root' })
export class GoalService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/goals`;

  mine(): Observable<PerformanceGoal[]> {
    return this.http.get<PerformanceGoal[]>(`${this.base}/me`);
  }

  team(): Observable<PerformanceGoal[]> {
    return this.http.get<PerformanceGoal[]>(`${this.base}/team`);
  }

  create(body: GoalCreate): Observable<PerformanceGoal> {
    return this.http.post<PerformanceGoal>(this.base, body);
  }

  updateSelf(goalId: string, body: GoalEmployeeUpdate): Observable<PerformanceGoal> {
    return this.http.patch<PerformanceGoal>(`${this.base}/${goalId}/self`, body);
  }

  updateAsManager(goalId: string, body: GoalManagerUpdate): Observable<PerformanceGoal> {
    return this.http.patch<PerformanceGoal>(`${this.base}/${goalId}`, body);
  }
}
