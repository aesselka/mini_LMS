import { Injectable, computed, inject } from '@angular/core';
import { AuthService, TOKEN_KEY } from '../services/auth.service';

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: 'student' | 'teacher' | 'admin';
}


@Injectable({ providedIn: 'root' })
export class Session {
  private auth = inject(AuthService);

  readonly user = computed<User | null>(() => this.auth.user());

  readonly token = computed<string | null>(() => {
    this.auth.user(); // пересчитываем токен при входе/выходе
    try {
      return localStorage.getItem(TOKEN_KEY);
    } catch {
      return null;
    }
  });

  isStudent(): boolean {
    return this.user()?.role === 'student';
  }
}