import { Component, inject, input, output, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { Session } from '../../core/session';
import { CourseService } from '../course-service';
import { errorText } from '../course';
import { TranslatePipe } from '../../services/translate.pipe';

@Component({
  selector: 'app-enroll-button',
  standalone: true,
  imports: [RouterLink, TranslatePipe],
  templateUrl: './enroll-button.html',
  styleUrl: './enroll-button.css',
})
export class EnrollButton {
  readonly courseId = input.required<number>();
  readonly enrolled = output<void>();

  protected session = inject(Session);
  protected courses = inject(CourseService);

  protected busy = signal(false);
  protected error = signal('');

  protected isEnrolled(): boolean {
    return this.courses.enrolledIds().has(this.courseId());
  }

  protected enroll(event: Event): void {
    event.stopPropagation();
    event.preventDefault();
    this.busy.set(true);
    this.error.set('');
    this.courses.enroll(this.courseId()).subscribe({
      next: () => { this.busy.set(false); this.enrolled.emit(); },
      error: err => {
        this.busy.set(false);
        this.error.set(errorText(err));
      },
    });
  }
}
