import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { DocumentScope, HrDocument } from '../models/document.models';

@Injectable({ providedIn: 'root' })
export class DocumentService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/documents`;

  mine(): Observable<HrDocument[]> {
    return this.http.get<HrDocument[]>(`${this.base}/me`);
  }

  upload(
    file: File,
    meta: { title: string; description?: string; scope: DocumentScope; owner_user_id?: string },
  ): Observable<HrDocument> {
    const form = new FormData();
    form.append('file', file);
    form.append('title', meta.title);
    form.append('scope', meta.scope);
    if (meta.description) {
      form.append('description', meta.description);
    }
    if (meta.owner_user_id) {
      form.append('owner_user_id', meta.owner_user_id);
    }
    return this.http.post<HrDocument>(this.base, form);
  }

  download(documentId: string): Observable<Blob> {
    return this.http.get(`${this.base}/${documentId}/content`, { responseType: 'blob' });
  }

  remove(documentId: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/${documentId}`);
  }
}
