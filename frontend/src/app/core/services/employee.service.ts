import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { EmployeeProfile, EmployeeSelfUpdate } from '../models/employee.models';

@Injectable({ providedIn: 'root' })
export class EmployeeService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/employees`;

  me(): Observable<EmployeeProfile> {
    return this.http.get<EmployeeProfile>(`${this.base}/me`);
  }

  updateMe(body: EmployeeSelfUpdate): Observable<EmployeeProfile> {
    return this.http.patch<EmployeeProfile>(`${this.base}/me`, body);
  }

  list(): Observable<EmployeeProfile[]> {
    return this.http.get<EmployeeProfile[]>(this.base);
  }
}
