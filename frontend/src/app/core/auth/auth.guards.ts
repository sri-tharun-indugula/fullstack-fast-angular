import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthService } from './auth.service';
import { Role, homePath } from './auth.models';

export const authGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  if (auth.user()) {
    return true;
  }
  return router.createUrlTree(['/login']);
};

export const guestGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  const user = auth.user();
  if (!user) {
    return true;
  }
  return router.createUrlTree([homePath(user.role)]);
};

export const homeRedirectGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  const user = auth.user();
  if (!user) {
    return router.createUrlTree(['/login']);
  }
  return router.createUrlTree([homePath(user.role)]);
};

export const roleGuard: CanActivateFn = (route) => {
  const auth = inject(AuthService);
  const router = inject(Router);
  const user = auth.user();
  if (!user) {
    return router.createUrlTree(['/login']);
  }
  const roles = route.data['roles'] as Role[] | undefined;
  if (!roles || roles.includes(user.role)) {
    return true;
  }
  return router.createUrlTree([homePath(user.role)]);
};
