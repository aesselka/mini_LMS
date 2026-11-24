import { Injectable, computed, inject, signal } from '@angular/core';
import { AuthService } from './auth.service';

// Цвета пиксельной капибары для аватара
export type AvatarColor = 'brown' | 'golden' | 'gray' | 'pink' | 'mint' | 'blue';

export type Avatar =
  | { kind: 'initials' } // буква имени в кружке (по умолчанию)
  | { kind: 'preset'; color: AvatarColor } // пиксельная капибара выбранного цвета
  | { kind: 'photo'; dataUrl: string }; // своё фото (уменьшенное до 160×160)

const PET_KEY = 'lms_pet';
const AVATARS_KEY = 'lms_avatars';

// Личные настройки пользователя: аватар и питомец-капибара.
// Хранятся в браузере (localStorage): аватар — отдельно для каждого пользователя.
@Injectable({ providedIn: 'root' })
export class PreferencesService {
  private auth = inject(AuthService);

  // ---------- капибара ----------
  readonly petEnabled = signal(localStorage.getItem(PET_KEY) !== 'off');

  setPetEnabled(enabled: boolean): void {
    this.petEnabled.set(enabled);
    localStorage.setItem(PET_KEY, enabled ? 'on' : 'off');
  }

  // ---------- аватар ----------
  private avatars = signal<Record<string, Avatar>>(this.readAvatars());

  // аватар текущего пользователя
  readonly avatar = computed<Avatar>(() => {
    const user = this.auth.user();
    return (user && this.avatars()[String(user.id)]) || { kind: 'initials' };
  });

  setAvatar(avatar: Avatar): void {
    const user = this.auth.user();
    if (!user) return;
    const next = { ...this.avatars(), [String(user.id)]: avatar };
    localStorage.setItem(AVATARS_KEY, JSON.stringify(next)); // может бросить ошибку, если память переполнена
    this.avatars.set(next);
  }

  // Своё фото: обрезаем по центру до квадрата и уменьшаем до 160×160, чтобы занимало мало места
  photoToDataUrl(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onerror = () => reject(new Error('read'));
      reader.onload = () => {
        const img = new Image();
        img.onerror = () => reject(new Error('image'));
        img.onload = () => {
          const size = 160;
          const side = Math.min(img.width, img.height);
          const canvas = document.createElement('canvas');
          canvas.width = size;
          canvas.height = size;
          const ctx = canvas.getContext('2d');
          if (!ctx) return reject(new Error('canvas'));
          ctx.drawImage(img, (img.width - side) / 2, (img.height - side) / 2, side, side, 0, 0, size, size);
          resolve(canvas.toDataURL('image/jpeg', 0.85));
        };
        img.src = reader.result as string;
      };
      reader.readAsDataURL(file);
    });
  }

  private readAvatars(): Record<string, Avatar> {
    try {
      return JSON.parse(localStorage.getItem(AVATARS_KEY) || '{}') as Record<string, Avatar>;
    } catch {
      return {};
    }
  }
}
