import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, switchMap, throwError } from 'rxjs';

import { AuthService } from './auth.service';

function isCredentialRequest(url: string): boolean {
  return url.includes('/auth/login') || url.includes('/auth/refresh') || url.includes('/auth/logout');
}

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const auth = inject(AuthService);
  const router = inject(Router);
  const token = auth.accessToken();
  const withCredentials = req.clone({ withCredentials: true });
  const authed =
    !isCredentialRequest(req.url) && token
      ? withCredentials.clone({ setHeaders: { Authorization: `Bearer ${token}` } })
      : withCredentials;

  return next(authed).pipe(
    catchError((error: unknown) => {
      if (
        !(error instanceof HttpErrorResponse) ||
        error.status !== 401 ||
        isCredentialRequest(req.url) ||
        req.headers.has('X-Retry')
      ) {
        return throwError(() => error);
      }
      return auth.refresh().pipe(
        switchMap(() => {
          const retryToken = auth.accessToken();
          return next(
            authed.clone({
              setHeaders: {
                Authorization: `Bearer ${retryToken ?? ''}`,
                'X-Retry': '1',
              },
            }),
          );
        }),
        catchError((refreshError: unknown) => {
          auth.clear();
          void router.navigateByUrl('/login');
          return throwError(() => refreshError);
        }),
      );
    }),
  );
};
