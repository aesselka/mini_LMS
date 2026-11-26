import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { TranslatePipe } from '../../services/translate.pipe';
import { AvatarView } from '../../components/avatar/avatar';
import { API_URL } from '../../services/api.config';

export interface TranscriptItem {
  code: string;
  title: string;
  credits: number;
  grade: string | null;
  teacher?: string;
}

export interface TranscriptResponse {
  gpa: number | null;
  courses: TranscriptItem[];
}

export interface AdminStats {
  students: number;
  teachers: number;
  admins: number;
  courses: number;
}

@Component({
  selector: 'app-profile',
  standalone: true,
  imports: [TranslatePipe, RouterLink, AvatarView],
  templateUrl: './profile.html'
})
export class Profile implements OnInit {
  protected auth = inject(AuthService);
  private http = inject(HttpClient);
  private router = inject(Router);

  // выход из аккаунта (кнопка в профиле)
  logout(): void {
    this.auth.logout();
    this.router.navigate(['/login']);
  }

  error = signal('');

  // Данные для студента (транскрипт, GPA, курсы, кредиты)
  transcriptData = signal<TranscriptResponse | null>(null);

  // Суммарные кредиты студента
  totalCredits = computed(() => {
    const list = this.transcriptData()?.courses ?? [];
    return list.reduce((sum, item) => sum + (item.credits || 0), 0);
  });

  // Данные для учителя (его курсы)
  teacherCourses = signal<any[]>([]);

  // Данные для админа (статистика системы)
  adminStats = signal<AdminStats | null>(null);

  // Редактирование профиля
  editing = signal(false);
  saving = signal(false);
  saveError = signal('');
  firstName = signal('');
  lastName = signal('');
  email = signal('');

  startEdit(): void {
    const u = this.auth.user();
    if (!u) return;
    this.firstName.set(u.first_name || '');
    this.lastName.set(u.last_name || '');
    this.email.set(u.email || '');
    this.saveError.set('');
    this.editing.set(true);
  }

  cancelEdit(): void {
    this.editing.set(false);
  }

  save(): void {
    this.saving.set(true);
    this.auth
      .updateProfile({
        first_name: this.firstName(),
        last_name: this.lastName(),
        email: this.email(),
      })
      .subscribe({
        next: () => {
          this.saving.set(false);
          this.editing.set(false);
        },
        error: (err: HttpErrorResponse) => {
          this.saving.set(false);
          const e = err.error;
          this.saveError.set(e?.email?.[0] || e?.detail || 'Could not save changes.');
        },
      });
  }

  ngOnInit(): void {
    this.auth.loadProfile().subscribe({
      next: (user) => {
        if (user.role === 'student') {
          // Загружаем транскрипт, курсы, GPA и кредиты студента
          this.http.get<TranscriptResponse>(`${API_URL}/transcript/`).subscribe({
            next: (res) => this.transcriptData.set(res),
            error: () => this.transcriptData.set(null),
          });
        } else if (user.role === 'teacher') {
          // Загружаем курсы, которые ведёт учитель
          this.http.get<any[]>(`${API_URL}/courses/`).subscribe({
            next: (courses) => {
              const fullName = `${user.first_name || ''} ${user.last_name || ''}`.trim();
              const filtered = courses.filter((c) => {
                const t = c.teacher;
                if (!t) return false;
                if (typeof t === 'object') {
                  return t.id === user.id || t.username === user.username;
                }
                return t === user.id || t === fullName || t === user.username || c.teacher_name === fullName;
              });
              this.teacherCourses.set(filtered);
            },
          });
        } else if (user.role === 'admin') {
          this.http.get<AdminStats>(`${API_URL}/auth/admin-stats/`).subscribe({
            next: (res) => this.adminStats.set(res),
            error: () => this.adminStats.set(null),
          });
        }
      },
      error: (err: HttpErrorResponse) => {
        if (err.status === 401) {
          this.auth.logout();
          this.router.navigate(['/login']);
        } else {
          this.error.set(err.status === 0 ? 'errors.network' : 'errors.unknown');
        }
      },
    });
  }
}