import { Component, computed, inject, input } from '@angular/core';
import { AuthService } from '../../services/auth.service';
import { Avatar, AvatarColor, PreferencesService } from '../../services/preferences.service';

// Голова пиксельной капибары для аватара (та же, что у питомца на сайте)
const HEAD = [
  '..OOO........OOO..',
  '.OBBBO......OBBBO.',
  '.OBDBOOOOOOOOBDBO.',
  '.OBBBBBBBBBBBBBBO.',
  '.OBBBBBBBBBBBBBBO.',
  'OBBBBBBBBBBBBBBBBO',
  'OBBBBBBBBBBBBBBBBO',
  'OBBBWEBBBBBBWEBBBO',
  'OBBBEEDDDDDDEEBBBO',
  'OBBBBBDNDDNDBBBBBO',
  'OBPPBBDDDDDDBBPPBO',
  'OBBBBBBBNNBBBBBBBO',
  'OBBBBBBBBBBBBBBBBO',
  '.OOOOOOOOOOOOOOOO.',
];

// Цвета шерсти и фона для каждого варианта аватара
export const AVATAR_COLORS: Record<AvatarColor, { fur: string; dark: string; bg: string }> = {
  brown: { fur: '#a0673a', dark: '#8a5530', bg: '#f3e3d3' },
  golden: { fur: '#d4a24c', dark: '#b3842f', bg: '#fbf0d6' },
  gray: { fur: '#8d8d94', dark: '#6f6f77', bg: '#e8e8ec' },
  pink: { fur: '#e29aab', dark: '#c97c8f', bg: '#fbe4ea' },
  mint: { fur: '#6fbf9c', dark: '#509f7d', bg: '#dcf3e9' },
  blue: { fur: '#7aa3d9', dark: '#5b86c0', bg: '#e0eaf8' },
};

interface Pixel {
  x: number;
  y: number;
  color: string;
}

export function headPixels(color: AvatarColor): Pixel[] {
  const c = AVATAR_COLORS[color];
  const palette: Record<string, string> = {
    O: '#3b2416',
    B: c.fur,
    D: c.dark,
    N: '#2a170c',
    E: '#1a1008',
    W: '#ffffff',
    P: '#e88a8a',
  };
  const pixels: Pixel[] = [];
  HEAD.forEach((row, y) =>
    [...row].forEach((ch, x) => {
      const fill = palette[ch];
      if (fill) pixels.push({ x, y, color: fill });
    }),
  );
  return pixels;
}

// Аватар пользователя: своё фото, пиксельная капибара или первая буква имени.
// Использование: <app-avatar [size]="64" />  (по умолчанию — аватар текущего пользователя)
//                <app-avatar [size]="48" [preview]="{ kind: 'preset', color: 'mint' }" />
@Component({
  selector: 'app-avatar',
  template: `
    @switch (current().kind) {
      @case ('photo') {
        <img class="av" [src]="photoUrl()" [style.width.px]="size()" [style.height.px]="size()" alt="" />
      }
      @case ('preset') {
        <span class="av" [style.width.px]="size()" [style.height.px]="size()" [style.background]="presetBg()">
          <svg viewBox="-1.5 -3 21 20" [attr.width]="size()" [attr.height]="size()" shape-rendering="crispEdges" aria-hidden="true">
            @for (p of presetPixels(); track $index) {
              <svg:rect [attr.x]="p.x" [attr.y]="p.y" width="1" height="1" [attr.fill]="p.color" />
            }
          </svg>
        </span>
      }
      @default {
        <span class="av initials" [style.width.px]="size()" [style.height.px]="size()" [style.font-size.px]="size() * 0.42">
          {{ letter() }}
        </span>
      }
    }
  `,
  styles: `
    :host {
      display: inline-flex;
      flex-shrink: 0;
    }
    .av {
      display: grid;
      place-items: center;
      overflow: hidden;
      border-radius: 50%;
      object-fit: cover;
      box-shadow: 0 0 0 1px var(--border);
    }
    .initials {
      background: var(--primary);
      color: var(--on-primary);
      font-weight: 700;
      line-height: 1;
    }
  `,
})
export class AvatarView {
  private auth = inject(AuthService);
  private prefs = inject(PreferencesService);

  readonly size = input(40);
  // показать конкретный вариант (для выбора в настройках); иначе — аватар текущего пользователя
  readonly preview = input<Avatar | null>(null);

  protected current = computed(() => this.preview() ?? this.prefs.avatar());

  protected photoUrl = computed(() => {
    const a = this.current();
    return a.kind === 'photo' ? a.dataUrl : '';
  });

  protected presetPixels = computed(() => {
    const a = this.current();
    return a.kind === 'preset' ? headPixels(a.color) : [];
  });

  protected presetBg = computed(() => {
    const a = this.current();
    return a.kind === 'preset' ? AVATAR_COLORS[a.color].bg : '';
  });

  protected letter = computed(() => {
    const u = this.auth.user();
    return (u?.first_name || u?.username || '?').charAt(0).toUpperCase();
  });
}
