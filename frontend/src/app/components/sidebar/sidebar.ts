import { Component, inject } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { LayoutService } from '../../services/layout.service';
import { Avatar } from '../../services/preferences.service';
import { TranslatePipe } from '../../services/translate.pipe';
import { AvatarView } from '../avatar/avatar';
import { Icon } from '../icon/icon';

// Боковое меню (для вошедших). На компьютере всегда видно слева, на телефоне выезжает по кнопке ☰.
@Component({
  selector: 'app-sidebar',
  imports: [RouterLink, RouterLinkActive, TranslatePipe, AvatarView, Icon],
  templateUrl: './sidebar.html',
  styleUrl: './sidebar.css',
})
export class Sidebar {
  protected auth = inject(AuthService);
  protected layout = inject(LayoutService);

  // логотип — коричневая капибара
  protected readonly logo: Avatar = { kind: 'preset', color: 'brown' };
}
