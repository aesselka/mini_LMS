import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { TranslatePipe } from '../../services/translate.pipe';

@Component({
  selector: 'app-profile',
  imports: [TranslatePipe],
  templateUrl: './profile.html',
})
export class Profile implements OnInit {
  protected auth = inject(AuthService);
  private router = inject(Router);

  error = signal('');

  ngOnInit(): void {
    // Обновляем данные с сервера: GET /api/auth/me/
    this.auth.loadProfile().subscribe({
      error: (err: HttpErrorResponse) => {
        if (err.status === 401) {
          // токен недействителен — выходим и отправляем на вход
          this.auth.logout();
          this.router.navigate(['/login']);
        } else {
          this.error.set(err.status === 0 ? 'errors.network' : 'errors.unknown');
        }
      },
    });
  }
}
