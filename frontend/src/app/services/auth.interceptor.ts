import { HttpInterceptorFn } from '@angular/common/http';
import { API_URL } from './api.config';
import { TOKEN_KEY } from './auth.service';

// Автоматически добавляет заголовок "Authorization: Token ..." ко всем запросам на бэкенд.
// Благодаря этому другим участникам (курсы, запись, админка) не нужно добавлять токен вручную.
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const token = localStorage.getItem(TOKEN_KEY);
  if (token && req.url.startsWith(API_URL)) {
    req = req.clone({ setHeaders: { Authorization: `Token ${token}` } });
  }
  return next(req);
};
