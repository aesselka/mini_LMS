import {
  Component,
  ElementRef,
  HostListener,
  computed,
  effect,
  inject,
  signal,
  untracked,
  viewChild,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AssistantService, ChatLink } from '../../services/assistant.service';
import { AuthService } from '../../services/auth.service';
import { I18nService } from '../../services/i18n.service';
import { TranslatePipe } from '../../services/translate.pipe';
import { Icon } from '../icon/icon';
import { CapyScene } from './capy-scene';

// Капи — капибара-помощник: круглая кнопка в правом нижнем углу и окно чата.
@Component({
  selector: 'app-assistant',
  imports: [FormsModule, TranslatePipe, Icon, CapyScene],
  templateUrl: './assistant.html',
  styleUrl: './assistant.css',
})
export class Assistant {
  protected chat = inject(AssistantService);
  private auth = inject(AuthService);
  private i18n = inject(I18nService);
  private router = inject(Router);

  private list = viewChild<ElementRef<HTMLElement>>('list');
  private field = viewChild<ElementRef<HTMLTextAreaElement>>('field');

  protected draft = '';
  // подсказка «Спроси меня!» над кнопкой, пока чат ни разу не открывали
  protected showHint = signal(!localStorage.getItem('lms_capy_seen'));

  protected greeting = computed(() => {
    this.i18n.lang();
    const user = this.auth.user();
    const name = user?.first_name || user?.username || '';
    return this.i18n.t('capy.hello', { name });
  });

  // быстрые вопросы (зависят от роли): значок + текст, который уйдёт в чат
  protected suggestions = computed(() => {
    this.i18n.lang();
    const items: [string, string][] =
      this.auth.user()?.role === 'teacher'
        ? [['📚', 'capy.q.courses'], ['⏰', 'capy.q.deadlines'], ['📝', 'capy.q.grade'], ['🍊', 'capy.q.who']]
        : [['📚', 'capy.q.courses'], ['🎓', 'capy.q.gpa'], ['⏰', 'capy.q.deadlines'], ['🎯', 'capy.q.final'], ['🍊', 'capy.q.who']];
    return items.map(([icon, key]) => ({ icon, text: this.i18n.t(key) }));
  });

  constructor() {
    // при открытии — убрать подсказку и поставить курсор в поле ввода
    effect(() => {
      if (!this.chat.open()) return;
      untracked(() => {
        localStorage.setItem('lms_capy_seen', '1');
        this.showHint.set(false);
      });
      setTimeout(() => this.field()?.nativeElement.focus());
    });

    // новое сообщение или «печатает…» — прокрутить вниз
    effect(() => {
      this.chat.messages();
      this.chat.loading();
      if (!this.chat.open()) return;
      setTimeout(() => {
        const el = this.list()?.nativeElement;
        if (el) el.scrollTop = el.scrollHeight;
      });
    });
  }

  send(text = this.draft): void {
    if (!text.trim()) return;
    this.chat.send(text);
    this.draft = '';
  }

  // Enter — отправить, Shift+Enter — новая строка
  onKeydown(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.send();
    }
  }

  go(link: ChatLink): void {
    this.router.navigateByUrl(link.url);
    // на телефоне чат закрывает всю страницу — закрываем, чтобы было видно, куда перешли
    if (window.innerWidth <= 640) this.chat.close();
  }

  @HostListener('document:keydown.escape')
  onEscape(): void {
    this.chat.close();
  }
}
