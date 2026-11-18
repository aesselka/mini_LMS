import { Component, input, output } from '@angular/core';
import { TranslatePipe } from '../../services/translate.pipe';

// Кнопка-глаз внутри поля пароля: показать / скрыть введённый пароль.
// Использование:
//   <span class="pw-field">
//     <input [type]="show() ? 'text' : 'password'" ... />
//     <app-eye-toggle [visible]="show()" (toggle)="show.set(!show())" />
//   </span>
@Component({
  selector: 'app-eye-toggle',
  imports: [TranslatePipe],
  template: `
    <button
      type="button"
      class="pw-toggle"
      [attr.aria-label]="(visible() ? 'password.hide' : 'password.show') | t"
      [attr.aria-pressed]="visible()"
      [title]="(visible() ? 'password.hide' : 'password.show') | t"
      (click)="toggle.emit()"
    >
      @if (visible()) {
        <!-- глаз зачёркнут: пароль сейчас виден, нажать — скрыть -->
        <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true">
          <path d="M3 3l18 18" />
          <path d="M10.6 10.6a2 2 0 0 0 2.8 2.8" />
          <path d="M9.4 5.2A9.8 9.8 0 0 1 12 5c5 0 9 4.5 10 7a12.6 12.6 0 0 1-3.1 4.2" />
          <path d="M6.2 6.7C4 8.1 2.6 10.2 2 12c1 2.5 5 7 10 7 1.9 0 3.6-.6 5-1.5" />
        </svg>
      } @else {
        <!-- открытый глаз: пароль скрыт, нажать — показать -->
        <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true">
          <path d="M2 12c1-2.5 5-7 10-7s9 4.5 10 7c-1 2.5-5 7-10 7S3 14.5 2 12z" />
          <circle cx="12" cy="12" r="3" />
        </svg>
      }
    </button>
  `,
})
export class EyeToggle {
  readonly visible = input(false);
  readonly toggle = output<void>();
}
