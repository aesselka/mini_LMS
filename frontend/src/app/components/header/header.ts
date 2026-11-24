import { Component, inject } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { I18nService } from '../../services/i18n.service';
import { LayoutService } from '../../services/layout.service';
import { Avatar } from '../../services/preferences.service';
import { ThemeService } from '../../services/theme.service';
import { TranslatePipe } from '../../services/translate.pipe';
import { AvatarView } from '../avatar/avatar';
import { Bell } from '../bell/bell';
import { Icon } from '../icon/icon';

// Верхняя панель: поиск (Ctrl+K), языки, тема, колокольчик и аватар.
// Для гостя — логотип и кнопки «Войти» / «Регистрация».
@Component({
  selector: 'app-header',
  imports: [RouterLink, RouterLinkActive, TranslatePipe, AvatarView, Bell, Icon],
  templateUrl: './header.html',
  styleUrl: './header.css',
})
export class Header {
  protected auth = inject(AuthService);
  protected i18n = inject(I18nService);
  protected theme = inject(ThemeService);
  protected layout = inject(LayoutService);

  protected readonly logo: Avatar = { kind: 'preset', color: 'brown' };
}
