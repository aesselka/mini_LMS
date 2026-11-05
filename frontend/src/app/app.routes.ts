import { Routes } from '@angular/router';
import { CourseList } from './catalog/course-list/course-list';
import { MyCourses } from './catalog/my-courses/my-courses';
import { CourseDetail } from './catalog/course-detail/course-detail';

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'courses' },
  { path: 'courses', component: CourseList },
  { path: 'my-courses', component: MyCourses },
  { path: 'courses/:id', component: CourseDetail },
  // /login and /register routes are added by the Login/Register author (feature/frontend-setup)
];
