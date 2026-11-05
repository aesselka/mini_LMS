import { Injectable, signal } from '@angular/core';

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: 'student' | 'teacher' | 'admin';
}

// Reads what the login page stored in localStorage:
//   'token' -> token.key from POST /api/auth/login/
//   'user'  -> JSON of response.user
// If the Login/Register author stores it under other keys, change them here only.
@Injectable({ providedIn: 'root' })
export class Session {
  readonly token = signal<string | null>(this.read('token'));
  readonly user = signal<User | null>(this.parseUser());

  private read(key: string): string | null {
    try { return localStorage.getItem(key); } catch { return null; }
  }

  private parseUser(): User | null {
    const raw = this.read('user');
    if (!raw) return null;
    try { return JSON.parse(raw) as User; } catch { return null; }
  }

  isStudent(): boolean {
    return this.user()?.role === 'student';
  }
}
