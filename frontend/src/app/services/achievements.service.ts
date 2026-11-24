import { HttpClient } from '@angular/common/http';
import { Injectable, computed, effect, inject, signal, untracked } from '@angular/core';
import { catchError, forkJoin, of } from 'rxjs';
import { Enrollment } from '../catalog/course';
import { CourseService } from '../catalog/course-service';
import { API_URL } from './api.config';
import { AuthService } from './auth.service';
import { I18nService } from './i18n.service';
import { PreferencesService } from './preferences.service';
import { ToastService } from './toast.service';

// Данные студента, из которых считаются достижения
interface Stats {
  courses: number; // на сколько курсов записан
  graded: number; // по скольким курсам уже есть оценка
  submissions: number; // сколько заданий сдано
  credits: number; // сумма кредитов
  gpa: number; // 0, пока нет оценок
}

interface AchievementDef {
  id: string;
  icon: string; // эмодзи
  target: number; // сколько нужно
  decimals?: number; // для GPA показываем 2 знака
  value: (s: Stats, local: { petClicks: number; searchUsed: boolean }) => number;
}

export interface Achievement {
  id: string;
  icon: string;
  titleKey: string; // ach.<id>.title
  descKey: string; // ach.<id>.desc
  value: number;
  target: number;
  decimals: number;
  unlocked: boolean;
  percent: number; // 0–100 для полоски прогресса
}

const DEFS: AchievementDef[] = [
  { id: 'firstCourse', icon: '🌱', target: 1, value: (s) => s.courses },
  { id: 'fullLoad', icon: '📚', target: 4, value: (s) => s.courses },
  { id: 'firstSubmission', icon: '✍️', target: 1, value: (s) => s.submissions },
  { id: 'hardWorker', icon: '💪', target: 5, value: (s) => s.submissions },
  { id: 'firstGrade', icon: '⭐', target: 1, value: (s) => s.graded },
  { id: 'credits15', icon: '🎯', target: 15, value: (s) => s.credits },
  { id: 'goodStudent', icon: '🎓', target: 3, decimals: 2, value: (s) => s.gpa },
  { id: 'honor', icon: '🏆', target: 3.67, decimals: 2, value: (s) => s.gpa },
  { id: 'explorer', icon: '🧭', target: 1, value: (_s, l) => (l.searchUsed ? 1 : 0) },
  { id: 'capyFriend', icon: '🤎', target: 10, value: (_s, l) => l.petClicks },
];

const REFRESH_EVERY_MS = 20_000;

// Достижения студента. Считаются из записей, транскрипта и сданных заданий + пара «весёлых» локальных.
// Когда открывается новое — капибара поздравляет всплывающим уведомлением.
@Injectable({ providedIn: 'root' })
export class AchievementsService {
  private http = inject(HttpClient);
  private auth = inject(AuthService);
  private courses = inject(CourseService);
  private prefs = inject(PreferencesService);
  private toast = inject(ToastService);
  private i18n = inject(I18nService);

  private stats = signal<Stats | null>(null);
  readonly loading = signal(false);
  private lastRefresh = 0;

  readonly achievements = computed<Achievement[]>(() => {
    const s = this.stats() ?? { courses: 0, graded: 0, submissions: 0, credits: 0, gpa: 0 };
    const local = { petClicks: this.prefs.petClicks(), searchUsed: this.prefs.searchUsed() };
    return DEFS.map((d) => {
      const value = d.value(s, local);
      return {
        id: d.id,
        icon: d.icon,
        titleKey: `ach.${d.id}.title`,
        descKey: `ach.${d.id}.desc`,
        value,
        target: d.target,
        decimals: d.decimals ?? 0,
        unlocked: value >= d.target,
        percent: Math.min(100, Math.round((value / d.target) * 100)),
      };
    });
  });

  readonly unlockedCount = computed(() => this.achievements().filter((a) => a.unlocked).length);

  constructor() {
    // следим за новыми достижениями (в том числе «погладил капибару» прямо сейчас)
    effect(() => {
      const list = this.achievements();
      const user = this.auth.user();
      if (!user || user.role !== 'student' || !this.stats()) return;
      untracked(() => this.celebrateNew(list, user.id));
    });
  }

  // загрузить данные с сервера (не чаще раза в 20 секунд, если не force)
  refresh(force = false): void {
    const user = this.auth.user();
    if (!user || user.role !== 'student') return;
    if (!force && Date.now() - this.lastRefresh < REFRESH_EVERY_MS) return;
    this.lastRefresh = Date.now();
    this.loading.set(true);

    forkJoin({
      enrollments: this.courses.myEnrollments().pipe(catchError(() => of([] as Enrollment[]))),
      transcript: this.http
        .get<{ total_credits: number; gpa: number | null }>(`${API_URL}/transcript/`)
        .pipe(catchError(() => of({ total_credits: 0, gpa: null }))),
      submissions: this.http.get<unknown[]>(`${API_URL}/submissions/`).pipe(catchError(() => of([] as unknown[]))),
    }).subscribe(({ enrollments, transcript, submissions }) => {
      this.stats.set({
        courses: enrollments.length,
        graded: enrollments.filter((e: Enrollment) => !!e.grade).length,
        submissions: submissions.length,
        credits: transcript.total_credits ?? 0,
        gpa: transcript.gpa ?? 0,
      });
      this.loading.set(false);
    });
  }

  // после выхода из аккаунта
  reset(): void {
    this.stats.set(null);
    this.lastRefresh = 0;
  }

  private celebrateNew(list: Achievement[], userId: number): void {
    const key = `lms_ach_seen_${userId}`;
    const stored = localStorage.getItem(key);
    const unlocked = list.filter((a) => a.unlocked).map((a) => a.id);

    // первый раз — просто запоминаем, чтобы не засыпать человека уведомлениями
    if (stored === null) {
      localStorage.setItem(key, JSON.stringify(unlocked));
      return;
    }

    const seen = new Set<string>(JSON.parse(stored) as string[]);
    const fresh = list.filter((a) => a.unlocked && !seen.has(a.id));
    if (!fresh.length) return;

    for (const a of fresh) {
      this.toast.show('ach.unlocked', { title: this.i18n.t(a.titleKey) }, 'achievement', a.icon, 6000);
      seen.add(a.id);
    }
    localStorage.setItem(key, JSON.stringify([...seen]));
  }
}
