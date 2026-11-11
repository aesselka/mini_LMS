import { Component, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { catchError, map, of, switchMap, tap } from 'rxjs';
import { Course, errorText, teacherName } from '../course';
import { CourseService } from '../course-service';
import { EnrollButton } from '../enroll-button/enroll-button';
import { Session } from '../../core/session';
import { TranslatePipe } from '../../services/translate.pipe';

@Component({
  selector: 'app-course-detail',
  standalone: true,
  imports: [RouterLink, EnrollButton, TranslatePipe],
  templateUrl: './course-detail.html',
  styleUrl: './course-detail.css',
})
export class CourseDetail {
  private api = inject(CourseService);
  private route = inject(ActivatedRoute);

  readonly course = signal<Course | null>(null);
  readonly loading = signal(true);
  readonly error = signal('');
  readonly teacherName = teacherName;

  constructor() {
    if (inject(Session).isStudent()) this.api.loadEnrolledIds();

    // reloads when the :id in the URL changes
    this.route.paramMap
      .pipe(
        map(p => Number(p.get('id'))),
        tap(() => { this.loading.set(true); this.error.set(''); }),
        switchMap(id =>
          this.api.getCourse(id).pipe(
            catchError(err => {
              this.error.set(err.status === 404 ? 'course.notFound' : errorText(err, 'course.loadError'));
              return of(null);
            }),
          ),
        ),
        takeUntilDestroyed(),
      )
      .subscribe(c => { this.course.set(c); this.loading.set(false); });
  }

  onEnrolled(): void {
    this.course.update(c => (c ? { ...c, students_count: c.students_count + 1 } : c));
  }
}
