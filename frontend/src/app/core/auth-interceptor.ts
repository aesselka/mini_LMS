import { HttpInterceptorFn } from '@angular/common/http';

// DRF TokenAuthentication expects: Authorization: Token <key>
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  let token: string | null = null;
  try { token = localStorage.getItem('token'); } catch { /* storage unavailable */ }
  return token ? next(req.clone({ setHeaders: { Authorization: `Token ${token}` } })) : next(req);
};
