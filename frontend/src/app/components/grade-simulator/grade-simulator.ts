import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';

// Response of GET /api/courses/my-standing/ (adjust fields to the real backend JSON)
interface CourseStanding {
  course_id: number;
  course_name: string;
  current_midterm_avg: number; // 0-100, weight 60%
}

type Zone = 'high' | 'ok' | 'risk';

// Set to false when the backend endpoint is ready
const USE_MOCK_DATA = true;

const MOCK_DATA: CourseStanding[] = [
  { course_id: 1, course_name: 'OOP and Design', current_midterm_avg: 75 },
  { course_id: 2, course_name: 'Databases', current_midterm_avg: 92 },
];

@Component({
  selector: 'app-grade-simulator',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <section class="sim">
      <h3>Final grade simulator</h3>

      <p *ngIf="loading()">Loading…</p>
      <p *ngIf="error()" class="err">{{ error() }}</p>

      <article *ngFor="let c of courses()" class="card" [ngClass]="zone(c)">
        <header>
          <strong>{{ c.course_name }}</strong>
          <span>Current midterm average: {{ c.current_midterm_avg | number:'1.0-1' }}</span>
        </header>

        <label>
          Expected final: <b>{{ expectedFinal[c.course_id] }}</b>
          <input type="range" min="0" max="100" step="1"
                 [(ngModel)]="expectedFinal[c.course_id]" />
        </label>

        <div class="result">
          Total: <b>{{ total(c) | number:'1.0-1' }}</b>
          <span class="badge">{{ label(c) }}</span>
        </div>
      </article>
    </section>
  `,
  styles: [`
    .sim { display: grid; gap: 12px; width: 100%; }
.card { box-sizing: border-box; width: 100%; padding: 16px; border-radius: 12px; border: 2px solid transparent;
        background: rgba(128,128,128,.12); transition: background .25s, border-color .25s; }
.card header { display: flex; flex-wrap: wrap; justify-content: space-between; gap: 12px; margin-bottom: 10px; }
    .card input[type=range] { width: 100%; }
    .result { margin-top: 8px; display: flex; gap: 10px; align-items: center; }
    .badge { padding: 2px 10px; border-radius: 999px; font-size: 13px; }

    .high { background: rgba(46,158,91,.18); border-color: #2e9e5b; }
    .high .badge { background: #2e9e5b; color: #fff; }
    .ok   { background: rgba(59,111,212,.18); border-color: #3b6fd4; }
    .ok .badge   { background: #3b6fd4; color: #fff; }
    .risk { background: rgba(211,58,47,.18); border-color: #d33a2f; }
    .risk .badge { background: #d33a2f; color: #fff; }
    .err  { color: #d33a2f; }
  `],
})
export class GradeSimulatorComponent implements OnInit {
  private http = inject(HttpClient);

  courses = signal<CourseStanding[]>([]);
  loading = signal(true);
  error = signal('');
  expectedFinal: Record<number, number> = {};

  ngOnInit(): void {
    if (USE_MOCK_DATA) {
      this.setCourses(MOCK_DATA);
      return;
    }

    this.http.get<CourseStanding[]>('/api/courses/my-standing/').subscribe({
      next: (data) => this.setCourses(data),
      error: () => {
        this.error.set('Failed to load course data');
        this.loading.set(false);
      },
    });
  }

  private setCourses(data: CourseStanding[]): void {
    data.forEach((c) => (this.expectedFinal[c.course_id] = 70));
    this.courses.set(data);
    this.loading.set(false);
  }

  // 60% midterm + 40% final
  total(c: CourseStanding): number {
    return c.current_midterm_avg * 0.6 + (this.expectedFinal[c.course_id] ?? 0) * 0.4;
  }

  zone(c: CourseStanding): Zone {
    const t = this.total(c);
    if (t >= 90) return 'high';
    if (t >= 70) return 'ok';
    return 'risk';
  }

  label(c: CourseStanding): string {
    return { high: 'Increased scholarship', ok: 'Scholarship', risk: 'At risk' }[this.zone(c)];
  }
}