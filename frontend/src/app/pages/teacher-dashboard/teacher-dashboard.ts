import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CourseStudent, TeacherCourse, TeacherService } from '../../services/teacher.service';
import { TranslatePipe } from '../../services/translate.pipe';

@Component({
  selector: 'app-teacher-dashboard',
  imports: [FormsModule, TranslatePipe],
  templateUrl: './teacher-dashboard.html',
  styleUrl: './teacher-dashboard.css',
})
export class TeacherDashboard implements OnInit {
  private api = inject(TeacherService);

  courses = signal<TeacherCourse[]>([]);
  selected = signal<TeacherCourse | null>(null);
  students = signal<CourseStudent[]>([]);
  error = signal('');
  savedId = signal<number | null>(null);
  form = { code: '', title: '', description: '', credits: 3 };

  ngOnInit(): void {
    this.loadCourses();
  }

  loadCourses(): void {
    this.api.myCourses().subscribe({
      next: (c) => this.courses.set(c),
      error: (e) => this.fail(e),
    });
  }

  createCourse(): void {
    this.error.set('');
    this.api.createCourse(this.form).subscribe({
      next: () => {
        this.form = { code: '', title: '', description: '', credits: 3 };
        this.loadCourses();
      },
      error: (e) => this.fail(e),
    });
  }

  deleteCourse(c: TeacherCourse): void {
    if (!confirm(`Delete ${c.code}?`)) return;
    this.api.deleteCourse(c.id).subscribe({
      next: () => {
        if (this.selected()?.id === c.id) this.selected.set(null);
        this.loadCourses();
      },
      error: (e) => this.fail(e),
    });
  }

  openCourse(c: TeacherCourse): void {
    this.selected.set(c);
    this.savedId.set(null);
    this.api.students(c.id).subscribe({
      next: (s) => this.students.set(s),
      error: (e) => this.fail(e),
    });
  }

  saveGrade(s: CourseStudent): void {
    this.error.set('');
    this.savedId.set(null);
    this.api.setGrade(s.id, s.grade ?? '').subscribe({
      next: () => this.savedId.set(s.id),
      error: (e) => this.fail(e),
    });
  }

  private fail(e: HttpErrorResponse): void {
    this.error.set(typeof e.error === 'object' ? JSON.stringify(e.error) : 'Error ' + e.status);
  }
}