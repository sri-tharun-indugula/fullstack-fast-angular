import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { Observable, finalize, of, share, tap, map, switchMap, catchError } from 'rxjs';

import { environment } from '../../../environments/environment';
import { LoginRequest, TokenResponse, UserPublic } from './auth.models';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly accessTokenState = signal<string | null>(null);
  private readonly userState = signal<UserPublic | null>(null);
  private refreshInFlight: Observable<UserPublic> | null = null;

  readonly accessToken = this.accessTokenState.asReadonly();
  readonly user = this.userState.asReadonly();
  readonly isAuthenticated = computed(() => this.userState() !== null && this.accessTokenState() !== null);

  login(body: LoginRequest): Observable<UserPublic> {
    return this.http
      .post<TokenResponse>(`${environment.apiUrl}/auth/login`, body, { withCredentials: true })
      .pipe(
        tap((token) => this.accessTokenState.set(token.access_token)),
        switchMap(() => this.loadMe()),
      );
  }

  refresh(): Observable<UserPublic> {
    if (this.refreshInFlight) {
      return this.refreshInFlight;
    }
    const request = this.http
      .post<TokenResponse>(`${environment.apiUrl}/auth/refresh`, {}, { withCredentials: true })
      .pipe(
        tap((token) => this.accessTokenState.set(token.access_token)),
        switchMap(() => this.loadMe()),
        finalize(() => {
          this.refreshInFlight = null;
        }),
        share(),
      );
    this.refreshInFlight = request;
    return request;
  }

  restoreSession(): Promise<void> {
    return new Promise((resolve) => {
      this.refresh().subscribe({
        next: () => resolve(),
        error: () => {
          this.clear();
          resolve();
        },
      });
    });
  }

  logout(): Observable<void> {
    return this.http.post(`${environment.apiUrl}/auth/logout`, {}, { withCredentials: true, responseType: 'text' }).pipe(
      catchError(() => of('')),
      map(() => undefined),
      finalize(() => this.clear()),
    );
  }

  clear(): void {
    this.accessTokenState.set(null);
    this.userState.set(null);
  }

  private loadMe(): Observable<UserPublic> {
    return this.http.get<UserPublic>(`${environment.apiUrl}/auth/me`).pipe(tap((user) => this.userState.set(user)));
  }
}
