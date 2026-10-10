import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { AppNotification, UnreadCount } from '../models/notification.models';

@Injectable({ providedIn: 'root' })
export class NotificationService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/notifications`;

  mine(unreadOnly = false): Observable<AppNotification[]> {
    const query = unreadOnly ? '?unread_only=true' : '';
    return this.http.get<AppNotification[]>(`${this.base}/me${query}`);
  }

  unreadCount(): Observable<UnreadCount> {
    return this.http.get<UnreadCount>(`${this.base}/unread-count`);
  }

  markRead(notificationId: string): Observable<AppNotification> {
    return this.http.patch<AppNotification>(`${this.base}/${notificationId}/read`, {});
  }

  markAllRead(): Observable<void> {
    return this.http.post<void>(`${this.base}/read-all`, {});
  }
}
