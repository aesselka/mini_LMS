import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { TranslatePipe } from '../../services/translate.pipe';

// Страница «Забыли пароль?»: пользователь вводит email, сервер отправляет ссылку для сброса.
@Component({
  selector: 'app-forgot-password',
  imports: [FormsModule, RouterLink, TranslatePipe],
  templateUrl: './forgot-password.html',
})
export class ForgotPassword {
  private auth = inject(AuthService);

  email = '';
  error = signal(''); // ключ перевода
  sent = signal(false);
  loading = signal(false);

  submit(): void {
    this.error.set('');
    const email = this.email.trim();

    if (!email) {
      this.error.set('errors.required');
      return;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      this.error.set('errors.emailInvalid');
      return;
    }

    this.loading.set(true);
    this.auth.requestPasswordReset(email).subscribe({
      // Сообщение одинаковое, есть такой email или нет — так нельзя узнать чужие email
      next: () => {
        this.loading.set(false);
        this.sent.set(true);
      },
      error: (err: HttpErrorResponse) => {
        this.loading.set(false);
        this.error.set(err.status === 0 ? 'errors.network' : 'errors.unknown');
      },
    });
  }
}
