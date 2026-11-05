import { Routes } from '@angular/router';
import { Login } from './pages/login/login';
import { Profile } from './pages/profile/profile';
import { Register } from './pages/register/register';
import { authGuard, guestGuard } from './services/auth.guard';

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'login' },

  // --- Участник 2: авторизация и профиль ---
  { path: 'login', component: Login, canActivate: [guestGuard] },
  { path: 'register', component: Register, canActivate: [guestGuard] },
  { path: 'profile', component: Profile, canActivate: [authGuard] },

  // --- Участник 4: каталог курсов (добавлять маршруты сюда) ---

  // --- Участник 5: админ-панель (добавлять маршруты сюда) ---

  { path: '**', redirectTo: '' },
];
