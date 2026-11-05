import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import { Observable, tap } from 'rxjs';
import { API_URL } from '../core/api';
import { Course, Enrollment } from './course';

@Injectable({ providedIn: 'root' })
export class CourseService {
  private http = inject(HttpClient);

  // ids of courses the current student is enrolled in (shared by list, detail and buttons)
  readonly enrolledIds = signal<ReadonlySet<number>>(new Set());

  loadEnrolledIds(): void {
    this.myEnrollments().subscribe({
      next: list => this.enrolledIds.set(new Set(list.map(e => e.course))),
      error: () => { /* not logged in or server down: buttons just show the default state */ },
    });
  }

  // GET /api/courses/?search=...  (public, search by title / code / teacher name)
  getCourses(search = ''): Observable<Course[]> {
    let params = new HttpParams();
    if (search.trim()) params = params.set('search', search.trim());
    return this.http.get<Course[]>(`${API_URL}/courses/`, { params });
  }

  // GET /api/courses/<id>/
  getCourse(id: number): Observable<Course> {
    return this.http.get<Course>(`${API_URL}/courses/${id}/`);
  }

  // GET /api/enrollments/  (for a student: only their own)
  myEnrollments(): Observable<Enrollment[]> {
    return this.http.get<Enrollment[]>(`${API_URL}/enrollments/`);
  }

  // DELETE /api/enrollments/<id>/  (student can delete only their own)
  unenroll(enrollmentId: number, courseId: number): Observable<void> {
    return this.http.delete<void>(`${API_URL}/enrollments/${enrollmentId}/`).pipe(
      tap(() => this.enrolledIds.update(ids => { const n = new Set(ids); n.delete(courseId); return n; })),
    );
  }

  // POST /api/enrollments/  body: {course: <id>}
  enroll(courseId: number): Observable<Enrollment> {
    return this.http
      .post<Enrollment>(`${API_URL}/enrollments/`, { course: courseId })
      .pipe(tap(() => this.enrolledIds.update(ids => new Set(ids).add(courseId))));
  }
}
