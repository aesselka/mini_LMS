import { Component, ElementRef, HostListener, inject, signal } from '@angular/core';
import { I18nService } from '../../services/i18n.service';
import { AppNotification, NotificationsService } from '../../services/notifications.service';
import { TranslatePipe } from '../../services/translate.pipe';
import { Icon } from '../icon/icon';

// Колокольчик уведомлений: счётчик непрочитанных и выпадающий список
@Component({
  selector: 'app-bell',
  imports: [TranslatePipe, Icon],
  templateUrl: './bell.html',
  styleUrl: './bell.css',
})
export class Bell {
  protected notifications = inject(NotificationsService);
  private i18n = inject(I18nService);
  private host = inject(ElementRef<HTMLElement>);

  protected open = signal(false);

  toggle(): void {
    this.open.update((o) => !o);
    if (this.open()) this.notifications.load(); // свежий список при открытии
  }

  read(n: AppNotification): void {
    if (!n.is_read) this.notifications.markRead(n.id);
  }

  // «5 минут назад», «2 дня назад» — на выбранном языке сайта
  timeAgo(iso: string): string {
    const locale = { en: 'en', ru: 'ru', kz: 'kk' }[this.i18n.lang()];
    const rtf = new Intl.RelativeTimeFormat(locale, { numeric: 'auto' });
    const seconds = Math.round((new Date(iso).getTime() - Date.now()) / 1000);
    const units: [Intl.RelativeTimeFormatUnit, number][] = [
      ['day', 86400],
      ['hour', 3600],
      ['minute', 60],
    ];
    for (const [unit, size] of units) {
      if (Math.abs(seconds) >= size) return rtf.format(Math.round(seconds / size), unit);
    }
    return rtf.format(0, 'minute');
  }

  // закрыть при клике мимо и по Escape
  @HostListener('document:click', ['$event'])
  onDocumentClick(event: MouseEvent): void {
    if (this.open() && !this.host.nativeElement.contains(event.target as Node)) this.open.set(false);
  }

  @HostListener('document:keydown.escape')
  onEscape(): void {
    this.open.set(false);
  }
}
