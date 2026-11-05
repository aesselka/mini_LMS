import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { Observable, tap } from 'rxjs';
import { API_URL } from './api.config';

export type Role = 'student' | 'teacher' | 'admin';

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: Role;
}

export interface AuthResponse {
  token: string;
  user: User;
}

export interface RegisterData {
  username: string;
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  role: 'student' | 'teacher';
}

export const TOKEN_KEY = 'lms_token';
const USER_KEY = 'lms_user';

// Работа с авторизацией: вход, регистрация, профиль, выход.
// Токен и пользователь хранятся в localStorage, чтобы не слетать после перезагрузки.
@Injectable({ providedIn: 'root' })
export class AuthService {
  private http = inject(HttpClient);

  private currentUser = signal<User | null>(this.readStoredUser());
  readonly user = this.currentUser.asReadonly();
  readonly isLoggedIn = computed(() => this.currentUser() !== null);

  login(username: string, password: string): Observable<AuthResponse> {
    return this.http
      .post<AuthResponse>(`${API_URL}/auth/login/`, { username, password })
      .pipe(tap((res) => this.saveSession(res)));
  }

  register(data: RegisterData): Observable<AuthResponse> {
    return this.http
      .post<AuthResponse>(`${API_URL}/auth/register/`, data)
      .pipe(tap((res) => this.saveSession(res)));
  }

  // Загружает свежие данные пользователя с сервера (GET /api/auth/me/)
  loadProfile(): Observable<User> {
    return this.http.get<User>(`${API_URL}/auth/me/`).pipe(
      tap((user) => {
        localStorage.setItem(USER_KEY, JSON.stringify(user));
        this.currentUser.set(user);
      }),
    );
  }

  logout(): void {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    this.currentUser.set(null);
  }

  private saveSession(res: AuthResponse): void {
    localStorage.setItem(TOKEN_KEY, res.token);
    localStorage.setItem(USER_KEY, JSON.stringify(res.user));
    this.currentUser.set(res.user);
  }

  private readStoredUser(): User | null {
    try {
      const raw = localStorage.getItem(USER_KEY);
      if (!raw || !localStorage.getItem(TOKEN_KEY)) return null;
      return JSON.parse(raw) as User;
    } catch {
      return null;
    }
  }
}
