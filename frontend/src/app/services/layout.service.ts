import { Injectable, signal } from '@angular/core';

// Общее состояние оболочки сайта: боковое меню на телефоне и окно быстрого поиска (Ctrl+K)
@Injectable({ providedIn: 'root' })
export class LayoutService {
  readonly menuOpen = signal(false); // боковое меню на телефоне
  readonly paletteOpen = signal(false); // окно поиска Ctrl+K

  toggleMenu(): void {
    this.menuOpen.update((open) => !open);
  }

  closeMenu(): void {
    this.menuOpen.set(false);
  }

  openPalette(): void {
    this.menuOpen.set(false);
    this.paletteOpen.set(true);
  }

  closePalette(): void {
    this.paletteOpen.set(false);
  }
}
