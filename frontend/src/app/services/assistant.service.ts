import { HttpClient } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import { API_URL } from './api.config';
import { I18nService } from './i18n.service';

export interface ChatLink {
  label: string;
  url: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  text: string;
  links?: ChatLink[];
  source?: 'ai' | 'rules';
  error?: boolean;
}

interface ChatResponse {
  reply: string;
  links: ChatLink[];
  source: 'ai' | 'rules';
}

// Чат с капибарой-помощником. История хранится, пока открыта вкладка
// (переходы между страницами её не стирают), и очищается при выходе.
@Injectable({ providedIn: 'root' })
export class AssistantService {
  private http = inject(HttpClient);
  private i18n = inject(I18nService);

  readonly open = signal(false);
  readonly messages = signal<ChatMessage[]>([]);
  readonly loading = signal(false);

  openChat(): void {
    this.open.set(true);
  }

  toggle(): void {
    this.open.update((o) => !o);
  }

  close(): void {
    this.open.set(false);
  }

  clear(): void {
    this.messages.set([]);
  }

  reset(): void {
    this.open.set(false);
    this.messages.set([]);
    this.loading.set(false);
  }

  send(text: string): void {
    const message = text.trim().slice(0, 500);
    if (!message || this.loading()) return;

    // последние 6 сообщений — чтобы ИИ понимал контекст разговора
    const history = this.messages()
      .filter((m) => !m.error)
      .slice(-6)
      .map((m) => ({ role: m.role, content: m.text }));

    this.messages.update((list) => [...list, { role: 'user', text: message }]);
    this.loading.set(true);

    this.http
      .post<ChatResponse>(`${API_URL}/assistant/chat/`, { message, lang: this.i18n.lang(), history })
      .subscribe({
        next: (res) => {
          this.loading.set(false);
          this.messages.update((list) => [
            ...list,
            { role: 'assistant', text: res.reply, links: res.links, source: res.source },
          ]);
        },
        error: () => {
          this.loading.set(false);
          this.messages.update((list) => [
            ...list,
            { role: 'assistant', text: this.i18n.t('capy.error'), error: true },
          ]);
        },
      });
  }
}
