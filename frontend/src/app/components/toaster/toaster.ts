import { Component, inject } from '@angular/core';
import { Avatar } from '../../services/preferences.service';
import { ToastService } from '../../services/toast.service';
import { TranslatePipe } from '../../services/translate.pipe';
import { AvatarView } from '../avatar/avatar';
import { Icon } from '../icon/icon';

// Всплывающие уведомления в правом верхнем углу. Для достижений — с капибарой.
@Component({
  selector: 'app-toaster',
  imports: [TranslatePipe, AvatarView, Icon],
  template: `
    <div class="stack" aria-live="polite">
      @for (t of toast.toasts(); track t.id) {
        <div [class]="'toast ' + t.kind" role="status">
          @if (t.kind === 'achievement') {
            <app-avatar [size]="40" [preview]="capy" />
            <div class="body">
              <strong>{{ t.icon }} {{ 'ach.newTitle' | t }}</strong>
              <span>{{ t.messageKey | t: t.params }}</span>
            </div>
          } @else {
            <span class="icon"><app-icon [name]="t.kind === 'success' ? 'check' : 'bell'" [size]="18" /></span>
            <div class="body">
              <span>{{ t.messageKey | t: t.params }}</span>
            </div>
          }
          <button type="button" class="close" [attr.aria-label]="'common.close' | t" (click)="toast.dismiss(t.id)">
            <app-icon name="x" [size]="16" />
          </button>
        </div>
      }
    </div>
  `,
  styles: `
    .stack {
      position: fixed;
      top: 76px;
      right: 16px;
      z-index: 100;
      display: flex;
      flex-direction: column;
      gap: 10px;
      width: 340px;
      max-width: calc(100vw - 32px);
      pointer-events: none;
    }
    .toast {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 12px 12px 12px 14px;
      border: 1px solid var(--border);
      border-radius: 14px;
      background: var(--surface);
      color: var(--text);
      box-shadow: 0 12px 30px rgba(0, 0, 0, 0.15);
      pointer-events: auto;
      animation: slide 0.25s ease-out;
    }
    .toast.achievement {
      border-color: var(--warning);
      background: linear-gradient(135deg, var(--surface), var(--primary-soft));
    }
    @keyframes slide {
      from {
        opacity: 0;
        transform: translateX(24px);
      }
    }
    .icon {
      display: grid;
      place-items: center;
      width: 32px;
      height: 32px;
      border-radius: 50%;
      background: var(--primary-soft);
      color: var(--primary);
    }
    .success .icon {
      color: var(--success);
    }
    .body {
      display: flex;
      flex-direction: column;
      gap: 2px;
      flex: 1;
      font-size: 14px;
    }
    .close {
      display: grid;
      place-items: center;
      padding: 4px;
      border: none;
      border-radius: 6px;
      background: none;
      color: var(--text-muted);
      cursor: pointer;
    }
    .close:hover {
      background: var(--surface-2);
    }
  `,
})
export class Toaster {
  protected toast = inject(ToastService);
  protected readonly capy: Avatar = { kind: 'preset', color: 'golden' };
}
