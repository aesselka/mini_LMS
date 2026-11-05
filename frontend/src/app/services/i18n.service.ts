import { HttpClient } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import { Observable, catchError, firstValueFrom, of, tap } from 'rxjs';

export type Lang = 'en' | 'ru' | 'kz';

const LANG_KEY = 'lms_lang';

// Мультиязычность: переводы лежат в public/i18n/{en,ru,kz}.json.
// Язык меняется "на лету" — без перезагрузки страницы — и запоминается в localStorage.
@Injectable({ providedIn: 'root' })
export class I18nService {
  private http = inject(HttpClient);

  readonly languages: Lang[] = ['en', 'ru', 'kz'];
  readonly lang = signal<Lang>(this.readStoredLang());
  private dictionary = signal<Record<string, string>>({});

  // Вызывается один раз при запуске приложения (см. app.config.ts)
  init(): Promise<unknown> {
    return firstValueFrom(this.load(this.lang()).pipe(catchError(() => of(null))));
  }

  // Переключение языка из шапки
  use(lang: Lang): void {
    this.load(lang).subscribe();
  }

  // Возвращает перевод по ключу; если перевода нет — сам ключ
  t(key: string): string {
    return this.dictionary()[key] ?? key;
  }

  private load(lang: Lang): Observable<Record<string, string>> {
    return this.http.get<Record<string, string>>(`/i18n/${lang}.json`).pipe(
      tap((dict) => {
        this.dictionary.set(dict);
        this.lang.set(lang);
        localStorage.setItem(LANG_KEY, lang);
        document.documentElement.lang = lang === 'kz' ? 'kk' : lang;
      }),
    );
  }

  private readStoredLang(): Lang {
    const saved = localStorage.getItem(LANG_KEY);
    return saved === 'en' || saved === 'ru' || saved === 'kz' ? saved : 'ru';
  }
}
