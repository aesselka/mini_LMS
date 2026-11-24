import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { API_URL } from './api.config';

export interface AppNotification {
  id: number;
  message: string;
  is_read: boolean;
  created_at: string;
}

const POLL_MS = 60_000; // обновлять раз в минуту

// Уведомления для колокольчика: GET /api/notifications/, отметка прочитанных
@Injectable({ providedIn: 'root' })
export class NotificationsService {
  private http = inject(HttpClient);

  readonly items = signal<AppNotification[]>([]);
  readonly unreadCount = computed(() => this.items().filter((n) => !n.is_read).length);
  readonly loadError = signal(false);

  private timer?: ReturnType<typeof setInterval>;

  // начать получать уведомления (после входа)
  start(): void {
    this.load();
    if (!this.timer) this.timer = setInterval(() => this.load(), POLL_MS);
  }

  // остановить и очистить (после выхода)
  stop(): void {
    clearInterval(this.timer);
    this.timer = undefined;
    this.items.set([]);
  }

  load(): void {
    this.http.get<AppNotification[]>(`${API_URL}/notifications/`).subscribe({
      next: (list) => {
        this.items.set(list);
        this.loadError.set(false);
      },
      error: () => this.loadError.set(true),
    });
  }

  markRead(id: number): void {
    // сразу отмечаем на экране, не дожидаясь сервера
    this.items.update((list) => list.map((n) => (n.id === id ? { ...n, is_read: true } : n)));
    this.http.post(`${API_URL}/notifications/${id}/read/`, {}).subscribe({ error: () => this.load() });
  }

  markAllRead(): void {
    this.items.update((list) => list.map((n) => ({ ...n, is_read: true })));
    this.http.post(`${API_URL}/notifications/read-all/`, {}).subscribe({ error: () => this.load() });
  }
}
