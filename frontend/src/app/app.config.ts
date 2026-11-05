import { provideHttpClient, withInterceptors } from '@angular/common/http';
import {
  ApplicationConfig,
  inject,
  provideAppInitializer,
  provideBrowserGlobalErrorListeners,
} from '@angular/core';
import { provideRouter } from '@angular/router';

import { routes } from './app.routes';
import { authInterceptor } from './services/auth.interceptor';
import { I18nService } from './services/i18n.service';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideRouter(routes),
    // HttpClient + автоматическое добавление токена к запросам
    provideHttpClient(withInterceptors([authInterceptor])),
    // загрузить переводы до первого показа страницы
    provideAppInitializer(() => inject(I18nService).init()),
  ],
};
