import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { PasswordStrength } from '../../components/password-strength/password-strength';
import { AuthService } from '../../services/auth.service';
import { TranslatePipe } from '../../services/translate.pipe';
import { EyeToggle } from '../../components/eye-toggle/eye-toggle';

// Страница «Новый пароль». Открывается по ссылке из письма:
// /reset-password?uid=...&token=...
@Component({
  selector: 'app-reset-password',
  imports: [FormsModule, RouterLink, TranslatePipe, PasswordStrength, EyeToggle],
  templateUrl: './reset-password.html',
})
export class ResetPassword {
  private auth = inject(AuthService);
  private route = inject(ActivatedRoute);

  private uid = this.route.snapshot.queryParamMap.get('uid') ?? '';
  private token = this.route.snapshot.queryParamMap.get('token') ?? '';

  // без uid и token в адресе ссылка заведомо неправильная
  linkInvalid = signal(!this.uid || !this.token);

  password = '';
  confirmPassword = '';
  showPassword = signal(false);
  showConfirm = signal(false); // глаз у поля «Повторите пароль»

  error = signal(''); // ключ перевода
  done = signal(false);
  loading = signal(false);

  submit(): void {
    this.error.set('');

    if (!this.password) {
      this.error.set('errors.required');
      return;
    }
    if (this.password.length < 8) {
      this.error.set('errors.passwordShort');
      return;
    }
    if (/^\d+$/.test(this.password)) {
      this.error.set('errors.passwordNumeric');
      return;
    }
    if (this.password !== this.confirmPassword) {
      this.error.set('errors.passwordMismatch');
      return;
    }

    this.loading.set(true);
    this.auth.confirmPasswordReset(this.uid, this.token, this.password).subscribe({
      next: () => {
        this.loading.set(false);
        this.done.set(true);
      },
      error: (err: HttpErrorResponse) => {
        this.loading.set(false);
        const body = (err.error ?? {}) as Record<string, unknown>;
        if (err.status === 400 && body['token']) {
          this.linkInvalid.set(true); // ссылка устарела или уже использована
        } else if (err.status === 400 && body['password']) {
          this.error.set('errors.passwordWeak'); // сервер счёл пароль слишком простым
        } else if (err.status === 0) {
          this.error.set('errors.network');
        } else {
          this.error.set('errors.unknown');
        }
      },
    });
  }
}
