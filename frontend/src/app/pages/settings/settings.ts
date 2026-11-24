import { Component, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { AvatarView } from '../../components/avatar/avatar';
import { I18nService } from '../../services/i18n.service';
import { Avatar, AvatarColor, PreferencesService } from '../../services/preferences.service';
import { ThemeService } from '../../services/theme.service';
import { TranslatePipe } from '../../services/translate.pipe';

const MAX_PHOTO_BYTES = 5 * 1024 * 1024; // 5 МБ

// Страница «Настройки»: аватар, тема, язык и питомец-капибара
@Component({
  selector: 'app-settings',
  imports: [RouterLink, TranslatePipe, AvatarView],
  templateUrl: './settings.html',
  styleUrl: './settings.css',
})
export class Settings {
  protected prefs = inject(PreferencesService);
  protected theme = inject(ThemeService);
  protected i18n = inject(I18nService);

  protected readonly colors: AvatarColor[] = ['brown', 'golden', 'gray', 'pink', 'mint', 'blue'];

  protected error = signal(''); // ключ перевода
  protected saved = signal(false); // короткое «Сохранено»
  private savedTimer?: ReturnType<typeof setTimeout>;

  // готовые варианты аватара для сетки выбора (создаются один раз)
  private readonly presets = new Map<AvatarColor, Avatar>(this.colors.map((color) => [color, { kind: 'preset', color }]));

  presetAvatar(color: AvatarColor): Avatar {
    return this.presets.get(color)!;
  }

  isSelected(color: AvatarColor): boolean {
    const a = this.prefs.avatar();
    return a.kind === 'preset' && a.color === color;
  }

  choosePreset(color: AvatarColor): void {
    this.save(() => this.prefs.setAvatar({ kind: 'preset', color }));
  }

  useInitials(): void {
    this.save(() => this.prefs.setAvatar({ kind: 'initials' }));
  }

  async onPhotoSelected(event: Event): Promise<void> {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    input.value = ''; // чтобы можно было выбрать тот же файл ещё раз
    this.error.set('');
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      this.error.set('settings.errors.notImage');
      return;
    }
    if (file.size > MAX_PHOTO_BYTES) {
      this.error.set('settings.errors.tooBig');
      return;
    }

    try {
      const dataUrl = await this.prefs.photoToDataUrl(file);
      this.save(() => this.prefs.setAvatar({ kind: 'photo', dataUrl }));
    } catch {
      this.error.set('settings.errors.photo');
    }
  }

  togglePet(): void {
    this.save(() => this.prefs.setPetEnabled(!this.prefs.petEnabled()));
  }

  private save(action: () => void): void {
    this.error.set('');
    try {
      action();
    } catch {
      this.error.set('settings.errors.storage'); // память браузера переполнена
      return;
    }
    this.saved.set(true);
    clearTimeout(this.savedTimer);
    this.savedTimer = setTimeout(() => this.saved.set(false), 1500);
  }
}
