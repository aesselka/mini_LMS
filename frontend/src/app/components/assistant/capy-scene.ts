import { Component, computed, input } from '@angular/core';
import { headPixels } from '../avatar/avatar';

interface Px {
  x: number;
  y: number;
  color: string;
}

// Мандарин на голове — капибары в японских горячих источниках (онсэнах)
// знамениты тем, что спокойно сидят с юдзу или мандарином на макушке.
const MANDARIN = [
  '...GG.',
  '.oooo.',
  'ohoooo',
  'oooood',
  '.oddo.',
];
const MANDARIN_COLORS: Record<string, string> = {
  G: '#4f9a3a',
  o: '#f28c28',
  h: '#ffc074',
  d: '#d36d12',
};

// Пиксельная Капи: просто голова с мандарином ('head')
// или сидит в горячем источнике по самый нос ('bath').
@Component({
  selector: 'app-capy-scene',
  template: `
    <svg
      [attr.viewBox]="viewBox()"
      [attr.width]="size()"
      [attr.height]="height()"
      shape-rendering="crispEdges"
      aria-hidden="true"
    >
      @for (p of pixels(); track $index) {
        <svg:rect [attr.x]="p.x" [attr.y]="p.y" width="1" height="1" [attr.fill]="p.color" />
      }
    </svg>
  `,
  styles: `
    :host {
      display: inline-block;
      line-height: 0;
    }
  `,
})
export class CapyScene {
  readonly size = input(48);
  readonly variant = input<'head' | 'bath'>('head');

  // пропорции картинки: 'bath' — 24×21 клетки, 'head' — 22×20
  protected height = computed(() => Math.round((this.size() * (this.variant() === 'bath' ? 21 : 20)) / (this.variant() === 'bath' ? 24 : 22)));

  protected viewBox = computed(() => (this.variant() === 'bath' ? '-3 -5 24 21' : '-2 -5 22 20'));

  protected pixels = computed<Px[]>(() => {
    const px: Px[] = [...headPixels('brown')];

    // мандарин лежит между ушами (верх головы — строка y = 2)
    MANDARIN.forEach((row, dy) =>
      [...row].forEach((ch, dx) => {
        if (MANDARIN_COLORS[ch]) px.push({ x: 6 + dx, y: -3 + dy, color: MANDARIN_COLORS[ch] });
      }),
    );

    if (this.variant() === 'bath') {
      // вода горячего источника: волнистая кромка и блики
      for (let x = -3; x < 21; x++) {
        const top = x % 4 === 0 ? 11 : 12;
        for (let y = top; y < 16; y++) {
          const foam = y === top;
          const glint = y === 14 && (x + 3) % 7 === 0;
          px.push({ x, y, color: foam ? '#bfeee9' : glint ? '#8fdcd5' : y < 14 ? '#3fb0a8' : '#2f948d' });
        }
      }
    }
    return px;
  });
}
