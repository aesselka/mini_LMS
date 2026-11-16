import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, map } from 'rxjs';
import { API_URL } from './api.config';
import { AuthService } from './auth.service';

export interface TeacherCourse {
  id: number;
  code: string;
  title: string;
  description: string | null;
  credits: number;
  students_count: number;
  teacher?: { id: number };
}

export interface CourseStudent {
  id: number;
  student: string;
  course: number;
  enroll_date: string;
  grade: string | null;
}

@Injectable({ providedIn: 'root' })
export class TeacherService {
  private http = inject(HttpClient);
  private auth = inject(AuthService);

  myCourses(): Observable<TeacherCourse[]> {
    const me = this.auth.user()?.id;
    return this.http
      .get<TeacherCourse[]>(`${API_URL}/courses/`)
      .pipe(map((list) => list.filter((c) => c.teacher?.id === me)));
  }

  createCourse(data: Partial<TeacherCourse>): Observable<TeacherCourse> {
    return this.http.post<TeacherCourse>(`${API_URL}/courses/`, data);
  }

  deleteCourse(id: number): Observable<void> {
    return this.http.delete<void>(`${API_URL}/courses/${id}/`);
  }

  students(courseId: number): Observable<CourseStudent[]> {
    return this.http
      .get<CourseStudent[]>(`${API_URL}/enrollments/`)
      .pipe(map((list) => list.filter((e) => e.course === courseId)));
  }

  setGrade(enrollmentId: number, grade: string): Observable<CourseStudent> {
    return this.http.patch<CourseStudent>(`${API_URL}/enrollments/${enrollmentId}/grade/`, { grade });
  }
}