import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { TranslatePipe } from '../../services/translate.pipe';

@Component({
  selector: 'app-login',
  imports: [FormsModule, RouterLink, TranslatePipe],
  templateUrl: './login.html',
})
export class Login {
  private auth = inject(AuthService);
  private router = inject(Router);

  username = '';
  password = '';

  // В error хранится КЛЮЧ перевода, чтобы ошибка тоже переводилась при смене языка
  error = signal('');
  loading = signal(false);

  submit(): void {
    this.error.set('');

    if (!this.username.trim() || !this.password) {
      this.error.set('errors.required');
      return;
    }

    this.loading.set(true);
    this.auth.login(this.username.trim(), this.password).subscribe({
     next: () => this.router.navigate([this.auth.homeRoute()]),
      error: (err: HttpErrorResponse) => {
        this.loading.set(false);
        if (err.status === 401 || err.status === 400) {
          this.error.set('errors.invalidCredentials');
        } else if (err.status === 0) {
          this.error.set('errors.network');
        } else {
          this.error.set('errors.unknown');
        }
      },
    });
  }
}
