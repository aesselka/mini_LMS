import { Component, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { forkJoin } from 'rxjs';
import { Course, Enrollment, errorText, teacherName } from '../course';
import { CourseService } from '../course-service';
import { Session } from '../../core/session';
import { TranslatePipe } from '../../services/translate.pipe';

interface Row { enrollment: Enrollment; course: Course | undefined; }

@Component({
  selector: 'app-my-courses',
  standalone: true,
  imports: [RouterLink, TranslatePipe],
  templateUrl: './my-courses.html',
  styleUrl: './my-courses.css',
})
export class MyCourses {
  private api = inject(CourseService);
  protected session = inject(Session);

  readonly rows = signal<Row[]>([]);
  readonly loading = signal(true);
  readonly error = signal('');
  readonly confirmId = signal<number | null>(null);   // enrollment waiting for "Yes, leave"
  readonly busyId = signal<number | null>(null);
  readonly rowError = signal('');
  readonly teacherName = teacherName;

  constructor() {
    if (!this.session.token()) { this.loading.set(false); return; }
    // the enrollment only has course id + title, so join with the course list for code / teacher
    forkJoin({ enrollments: this.api.myEnrollments(), courses: this.api.getCourses() }).subscribe({
      next: ({ enrollments, courses }) => {
        const byId = new Map(courses.map(c => [c.id, c]));
        this.rows.set(enrollments.map(e => ({ enrollment: e, course: byId.get(e.course) })));
        this.loading.set(false);
      },
      error: err => {
        this.error.set(errorText(err, 'myCourses.loadError'));
        this.loading.set(false);
      },
    });
  }

  leave(row: Row): void {
    this.busyId.set(row.enrollment.id);
    this.rowError.set('');
    this.api.unenroll(row.enrollment.id, row.enrollment.course).subscribe({
      next: () => {
        this.rows.update(list => list.filter(r => r.enrollment.id !== row.enrollment.id));
        this.busyId.set(null);
        this.confirmId.set(null);
      },
      error: err => { this.busyId.set(null); this.rowError.set(errorText(err)); },
    });
  }
}
