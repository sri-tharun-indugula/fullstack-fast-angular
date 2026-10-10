import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { authInterceptor } from './auth.interceptor';
import { AuthService } from './auth.service';
import { UserPublic } from './auth.models';

describe('AuthService', () => {
  let service: AuthService;
  let http: HttpTestingController;

  const user: UserPublic = {
    id: '6f1b0d3e-1a2b-4c3d-8e9f-001122334455',
    email: 'admin@example.com',
    full_name: 'System Admin',
    role: 'admin',
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideRouter([]), provideHttpClient(withInterceptors([authInterceptor])), provideHttpClientTesting()],
    });
    service = TestBed.inject(AuthService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    http.verify();
  });

  it('keeps the access token in memory and loads the current user', () => {
    let signedIn: UserPublic | undefined;
    service.login({ email: user.email, password: 'secret' }).subscribe((value) => {
      signedIn = value;
    });

    const login = http.expectOne('/api/v1/auth/login');
    expect(login.request.withCredentials).toBe(true);
    login.flush({ access_token: 'access-1', token_type: 'bearer', expires_in: 900 });

    const me = http.expectOne('/api/v1/auth/me');
    expect(me.request.headers.get('Authorization')).toBe('Bearer access-1');
    me.flush(user);

    expect(signedIn).toEqual(user);
    expect(service.accessToken()).toBe('access-1');
    expect(service.user()).toEqual(user);
    expect(window.localStorage.getItem('access_token')).toBeNull();
  });
});
