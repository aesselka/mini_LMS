import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService, RegisterData } from '../../services/auth.service';
import { TranslatePipe } from '../../services/translate.pipe';

@Component({
  selector: 'app-register',
  imports: [FormsModule, RouterLink, TranslatePipe],
  templateUrl: './register.html',
})
export class Register {
  private auth = inject(AuthService);
  private router = inject(Router);

  form: RegisterData = {
    username: '',
    email: '',
    password: '',
    first_name: '',
    last_name: '',
    role: 'student',
  };
  confirmPassword = '';

  error = signal(''); // ключ перевода
  serverErrors = signal<string[]>([]); // сообщения от бэкенда (например, "username уже занят")
  loading = signal(false);

  submit(): void {
    this.error.set('');
    this.serverErrors.set([]);

    const f = this.form;
    if (!f.username.trim() || !f.email.trim() || !f.password) {
      this.error.set('errors.required');
      return;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(f.email.trim())) {
      this.error.set('errors.emailInvalid');
      return;
    }
    if (f.password.length < 8) {
      this.error.set('errors.passwordShort');
      return;
    }
    if (/^\d+$/.test(f.password)) {
      this.error.set('errors.passwordNumeric');
      return;
    }
    if (f.password !== this.confirmPassword) {
      this.error.set('errors.passwordMismatch');
      return;
    }

    this.loading.set(true);
    this.auth
      .register({ ...f, username: f.username.trim(), email: f.email.trim() })
      .subscribe({
        // бэкенд сразу возвращает токен, поэтому после регистрации пользователь уже вошёл
     next: (res) => {
  this.auth['saveSession'](res); // или сохраните токен/пользователя явно
  this.router.navigate([this.auth.homeRoute()]);
},
        error: (err: HttpErrorResponse) => {
          this.loading.set(false);
          if (err.status === 400 && err.error && typeof err.error === 'object') {
            // Django возвращает ошибки по полям: { "username": ["..."], "email": ["..."] }
                        const messages = Object.entries(err.error as Record<string, unknown>).map(([field, value]) => {
              const text = Array.isArray(value) ? value.join(' ') : String(value);
              // известные ошибки сервера переводим, остальные показываем как есть
              if (field === 'username' && text.includes('already exists')) return 'errors.usernameTaken';
              if (field === 'password') return 'errors.passwordWeak';
              return `${field}: ${text}`;
            });
            this.serverErrors.set(messages);
          } else if (err.status === 0) {
            this.error.set('errors.network');
          } else {
            this.error.set('errors.unknown');
          }
        },
      });
  }
}
