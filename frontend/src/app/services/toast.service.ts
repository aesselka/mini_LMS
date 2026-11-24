import { Injectable, signal } from '@angular/core';

export interface Toast {
  id: number;
  messageKey: string; // ключ перевода
  params?: Record<string, string | number>; // параметры для перевода
  kind: 'success' | 'info' | 'achievement';
  icon?: string; // эмодзи для достижений
}

// Всплывающие уведомления в правом верхнем углу (исчезают сами через несколько секунд).
// Использование: toast.show('settings.saved')  или  toast.show('ach.unlocked', { title: '...' }, 'achievement', '🏆')
@Injectable({ providedIn: 'root' })
export class ToastService {
  readonly toasts = signal<Toast[]>([]);
  private nextId = 1;

  show(
    messageKey: string,
    params?: Record<string, string | number>,
    kind: Toast['kind'] = 'success',
    icon?: string,
    durationMs = 4500,
  ): void {
    const toast: Toast = { id: this.nextId++, messageKey, params, kind, icon };
    this.toasts.update((list) => [...list, toast].slice(-4)); // не больше 4 сразу
    setTimeout(() => this.dismiss(toast.id), durationMs);
  }

  dismiss(id: number): void {
    this.toasts.update((list) => list.filter((t) => t.id !== id));
  }
}
