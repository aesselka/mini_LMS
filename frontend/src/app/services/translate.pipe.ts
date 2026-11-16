import { Pipe, PipeTransform, inject } from '@angular/core';
import { I18nService } from './i18n.service';

// Использование в шаблоне: {{ 'login.title' | t }}
// С параметрами: {{ 'catalog.count' | t: { n: 5 } }}
// pure: false — чтобы текст обновлялся сразу после смены языка
@Pipe({ name: 't', pure: false })
export class TranslatePipe implements PipeTransform {
  private i18n = inject(I18nService);

  transform(key: string, params?: Record<string, string | number>): string {
    return this.i18n.t(key, params);
  }
}
