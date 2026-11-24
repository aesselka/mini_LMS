import { Component, effect, inject } from '@angular/core';
import { NavigationEnd, Router, RouterOutlet } from '@angular/router';
import { filter } from 'rxjs';
import { CapybaraPet } from './components/capybara-pet/capybara-pet';
import { CommandPalette } from './components/command-palette/command-palette';
import { Header } from './components/header/header';
import { Sidebar } from './components/sidebar/sidebar';
import { Toaster } from './components/toaster/toaster';
import { AchievementsService } from './services/achievements.service';
import { AuthService } from './services/auth.service';
import { NotificationsService } from './services/notifications.service';
import { PreferencesService } from './services/preferences.service';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, Header, Sidebar, CommandPalette, Toaster, CapybaraPet],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App {
  protected auth = inject(AuthService);
  protected prefs = inject(PreferencesService);
  private notifications = inject(NotificationsService);
  private achievements = inject(AchievementsService);

  constructor() {
    // вошёл — получаем уведомления и считаем достижения; вышел — всё очищаем
    effect(() => {
      if (this.auth.isLoggedIn()) {
        this.notifications.start();
        this.achievements.refresh(true);
      } else {
        this.notifications.stop();
        this.achievements.reset();
      }
    });

    // при переходах между страницами — обновить достижения (не чаще раза в 20 секунд)
    inject(Router)
      .events.pipe(filter((e) => e instanceof NavigationEnd))
      .subscribe(() => this.achievements.refresh());
  }
}
