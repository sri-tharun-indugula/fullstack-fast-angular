import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { Department, DepartmentCreate } from '../models/employee.models';

@Injectable({ providedIn: 'root' })
export class DepartmentService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/departments`;

  list(): Observable<Department[]> {
    return this.http.get<Department[]>(this.base);
  }

  create(body: DepartmentCreate): Observable<Department> {
    return this.http.post<Department>(this.base, body);
  }
}
