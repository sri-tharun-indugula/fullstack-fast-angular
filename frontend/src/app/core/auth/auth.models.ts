export type Role = 'admin' | 'manager' | 'employee';

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: 'bearer';
  expires_in: number;
}

export interface UserPublic {
  id: string;
  email: string;
  full_name: string;
  role: Role;
}

export function homePath(role: Role): string {
  switch (role) {
    case 'admin':
      return '/admin';
    case 'manager':
      return '/manager';
    case 'employee':
      return '/employee';
  }
}
