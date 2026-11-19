import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { TranslatePipe } from '../../services/translate.pipe';
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

@Component({
  selector: 'app-profile',
  standalone: true,
  imports: [TranslatePipe, RouterLink],
  templateUrl: './profile.html'
})
export class Profile implements OnInit {
  protected auth = inject(AuthService);
  private http = inject(HttpClient);
  private router = inject(Router);

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

  ngOnInit(): void {
    this.auth.loadProfile().subscribe({
      next: (user) => {
        if (user.role === 'student') {
          // Загружаем транскрипт, курсы, GPA и кредиты студента
          this.http.get<TranscriptResponse>(`${API_URL}/transcript/`).subscribe({
            next: (res) => this.transcriptData.set(res),
            error: () => this.transcriptData.set(null)
          });
        } else if (user.role === 'teacher') {
          // Загружаем курсы, которые ведет учитель
          this.http.get<any[]>(`${API_URL}/courses/`).subscribe({
          next: (courses) => {
  const fullName = `${user.first_name || ''} ${user.last_name || ''}`.trim();
  const filtered = courses.filter(c => {
    const t = c.teacher;
    if (!t) return false;
    if (typeof t === 'object') {
      return t.id === user.id || t.username === user.username;
    }
    return t === user.id || t === fullName || t === user.username || c.teacher_name === fullName;
  });
  this.teacherCourses.set(filtered);
}
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
      }
    });
  }
}