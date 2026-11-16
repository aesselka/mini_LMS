import { Component, DestroyRef, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ReactiveFormsModule, FormControl } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { catchError, debounceTime, distinctUntilChanged, of, startWith, switchMap, tap } from 'rxjs';
import { Course, errorText, teacherName } from '../course';
import { CourseService } from '../course-service';
import { EnrollButton } from '../enroll-button/enroll-button';
import { Session } from '../../core/session';
import { TranslatePipe } from '../../services/translate.pipe';

@Component({
  selector: 'app-course-list',
  standalone: true,
  imports: [ReactiveFormsModule, RouterLink, EnrollButton, TranslatePipe],
  templateUrl: './course-list.html',
  styleUrl: './course-list.css',
})
export class CourseList {
  private api = inject(CourseService);
  private destroyRef = inject(DestroyRef);
  protected session = inject(Session);

  readonly search = new FormControl('', { nonNullable: true });
  readonly courses = signal<Course[]>([]);
  readonly loading = signal(true);
  readonly error = signal('');
  readonly teacherName = teacherName;

  constructor() {
    if (this.session.isStudent()) this.api.loadEnrolledIds();

    // live search: wait 300 ms after typing, drop repeats, cancel the previous request
    this.search.valueChanges
      .pipe(
        debounceTime(300),
        startWith(this.search.value),
        distinctUntilChanged(),
        tap(() => { this.loading.set(true); this.error.set(''); }),
        switchMap(q =>
          this.api.getCourses(q).pipe(
            catchError(err => { this.error.set(errorText(err, 'catalog.loadError')); return of([] as Course[]); }),
          ),
        ),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe(list => { this.courses.set(list); this.loading.set(false); });
  }

  clear(): void { this.search.setValue(''); }

  // after enrolling, bump the counter on the card without refetching
  onEnrolled(id: number): void {
    this.courses.update(list => list.map(c => (c.id === id ? { ...c, students_count: c.students_count + 1 } : c)));
  }
}
