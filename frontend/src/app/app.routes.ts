import { Routes } from '@angular/router';

import { TeacherDashboard } from './pages/teacher-dashboard/teacher-dashboard';
import { teacherGuard } from './services/role.guard';

import { CourseList } from './catalog/course-list/course-list';
import { CourseDetail } from './catalog/course-detail/course-detail';
import { MyCourses } from './catalog/my-courses/my-courses';

import { Login } from './pages/login/login';
import { Profile } from './pages/profile/profile';
import { Register } from './pages/register/register';
import { authGuard, guestGuard } from './services/auth.guard';

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'login' },

  { path: 'login', component: Login, canActivate: [guestGuard] },
  { path: 'register', component: Register, canActivate: [guestGuard] },
  { path: 'profile', component: Profile, canActivate: [authGuard] },

  { path: 'courses', component: CourseList, canActivate: [authGuard] },
  { path: 'courses/:id', component: CourseDetail, canActivate: [authGuard] },
  { path: 'my-courses', component: MyCourses, canActivate: [authGuard] },

  { path: 'teacher', component: TeacherDashboard, canActivate: [authGuard, teacherGuard] },

  { path: '**', redirectTo: '' },
];


