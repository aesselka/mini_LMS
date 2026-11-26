import { Component, ElementRef, HostListener, computed, effect, inject, signal, viewChild } from '@angular/core';
import { Router } from '@angular/router';
import { Course } from '../../catalog/course';
import { CourseService } from '../../catalog/course-service';
import { AssistantService } from '../../services/assistant.service';
import { AuthService } from '../../services/auth.service';
import { I18nService, Lang } from '../../services/i18n.service';
import { LayoutService } from '../../services/layout.service';
import { PreferencesService } from '../../services/preferences.service';
import { ThemeService } from '../../services/theme.service';
import { TranslatePipe } from '../../services/translate.pipe';
import { Icon } from '../icon/icon';

interface PaletteItem {
  group: 'pages' | 'courses' | 'actions';
  label: string; // уже переведённый текст
  hint?: string; // серый текст справа (код курса, преподаватель)
  icon: string;
  search: string; // по чему ищем (в нижнем регистре)
  run: () => void;
}

const GROUP_ORDER: PaletteItem['group'][] = ['pages', 'courses', 'actions'];

// Быстрый поиск по Ctrl+K: страницы, курсы и действия (тема, язык).
// Управление: ↑ ↓ — выбор, Enter — открыть, Esc — закрыть.
@Component({
  selector: 'app-command-palette',
  imports: [TranslatePipe, Icon],
  templateUrl: './command-palette.html',
  styleUrl: './command-palette.css',
})
export class CommandPalette {
  protected layout = inject(LayoutService);
  private auth = inject(AuthService);
  private router = inject(Router);
  private courseService = inject(CourseService);
  private i18n = inject(I18nService);
  private theme = inject(ThemeService);
  private prefs = inject(PreferencesService);
  private assistant = inject(AssistantService);

  private input = viewChild<ElementRef<HTMLInputElement>>('searchInput');

  protected query = signal('');
  protected active = signal(0);
  private courses = signal<Course[]>([]);
  private coursesLoaded = false;

  constructor() {
    // при открытии: очистить запрос, загрузить курсы (один раз) и поставить курсор в поле
    effect(() => {
      if (!this.layout.paletteOpen()) return;
      this.query.set('');
      this.active.set(0);
      this.prefs.markSearchUsed();
      if (!this.coursesLoaded) {
        this.coursesLoaded = true;
        this.courseService.getCourses().subscribe({
          next: (list) => this.courses.set(list),
          error: () => (this.coursesLoaded = false),
        });
      }
      setTimeout(() => this.input()?.nativeElement.focus());
    });
  }

  // все варианты (на текущем языке)
  private allItems = computed<PaletteItem[]>(() => {
    this.i18n.lang(); // пересчитать при смене языка
    const t = (key: string) => this.i18n.t(key);
    const role = this.auth.user()?.role;
    const go = (path: string) => () => this.router.navigate([path]);

    const pages: PaletteItem[] = [
      { group: 'pages', label: t('nav.courses'), icon: 'book', search: '', run: go('/courses') },
      { group: 'pages', label: t('nav.my_courses'), icon: 'bookmark', search: '', run: go('/my-courses') },
      { group: 'pages', label: t('nav.profile'), icon: 'user', search: '', run: go('/profile') },
      { group: 'pages', label: t('nav.settings'), icon: 'settings', search: '', run: go('/settings') },
    ];
    if (role === 'student') {
      pages.push({ group: 'pages', label: t('nav.achievements'), icon: 'trophy', search: '', run: go('/achievements') });
    }
    if (role === 'teacher') {
      pages.push({ group: 'pages', label: t('nav.cabinet'), icon: 'briefcase', search: '', run: go('/teacher') });
    }

    const courses: PaletteItem[] = this.courses().map((c) => {
      const teacher = c.teacher ? `${c.teacher.first_name} ${c.teacher.last_name}`.trim() || c.teacher.username : '';
      return {
        group: 'courses',
        label: c.title,
        hint: c.code,
        icon: 'book',
        search: `${c.code} ${teacher}`,
        run: () => this.router.navigate(['/courses', c.id]),
      };
    });

    const langs: [Lang, string][] = [
      ['en', 'English'],
      ['ru', 'Русский'],
      ['kz', 'Қазақша'],
    ];
    const actions: PaletteItem[] = [
      {
        group: 'actions',
        label: t('capy.ask'),
        icon: 'chat',
        search: 'ai ии капи capy капибара помощник assistant көмекші chat чат',
        run: () => this.assistant.openChat(),
      },
      {
        group: 'actions',
        label: t(this.theme.theme() === 'dark' ? 'theme.toLight' : 'theme.toDark'),
        icon: this.theme.theme() === 'dark' ? 'sun' : 'moon',
        search: 'theme тема тақырып dark light',
        run: () => this.theme.toggle(),
      },
      ...langs.map(
        ([code, name]): PaletteItem => ({
          group: 'actions',
          label: `${t('settings.language')}: ${name}`,
          icon: 'globe',
          search: `language язык тіл ${code}`,
          run: () => this.i18n.use(code),
        }),
      ),
    ];

    return [...pages, ...courses, ...actions].map((item) => ({
      ...item,
      search: `${item.label} ${item.search}`.toLowerCase(),
    }));
  });

  // отфильтрованные по запросу; без запроса — страницы и действия, курсы только первые 5
  protected results = computed<PaletteItem[]>(() => {
    const q = this.query().trim().toLowerCase();
    const items = this.allItems();
    if (!q) {
      return [
        ...items.filter((i) => i.group === 'pages'),
        ...items.filter((i) => i.group === 'courses').slice(0, 5),
        ...items.filter((i) => i.group === 'actions'),
      ];
    }
    const words = q.split(/\s+/);
    return items.filter((i) => words.every((w) => i.search.includes(w)));
  });

  // результаты по группам — для заголовков «Страницы», «Курсы», «Действия»
  protected groups = computed(() =>
    GROUP_ORDER.map((group) => ({ group, items: this.results().filter((i) => i.group === group) })).filter(
      (g) => g.items.length,
    ),
  );

  // порядковый номер элемента во всём списке (для подсветки стрелками)
  indexOf(item: PaletteItem): number {
    return this.results().indexOf(item);
  }

  onInput(value: string): void {
    this.query.set(value);
    this.active.set(0);
  }

  run(item: PaletteItem): void {
    this.layout.closePalette();
    item.run();
  }

  onKeydown(event: KeyboardEvent): void {
    const count = this.results().length;
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      this.active.set(count ? (this.active() + 1) % count : 0);
      this.scrollActiveIntoView();
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      this.active.set(count ? (this.active() - 1 + count) % count : 0);
      this.scrollActiveIntoView();
    } else if (event.key === 'Enter') {
      event.preventDefault();
      const item = this.results()[this.active()];
      if (item) this.run(item);
    }
  }

  private scrollActiveIntoView(): void {
    setTimeout(() => document.querySelector('.palette .option.active')?.scrollIntoView({ block: 'nearest' }));
  }

  // Ctrl+K (или ⌘K на Mac) — открыть/закрыть; Esc — закрыть
  @HostListener('document:keydown', ['$event'])
  onGlobalKeydown(event: KeyboardEvent): void {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
      if (!this.auth.isLoggedIn()) return;
      event.preventDefault();
      if (this.layout.paletteOpen()) this.layout.closePalette();
      else this.layout.openPalette();
    } else if (event.key === 'Escape' && this.layout.paletteOpen()) {
      this.layout.closePalette();
    }
  }
}
