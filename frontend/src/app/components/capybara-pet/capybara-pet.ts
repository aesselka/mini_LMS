import { Component, OnDestroy, OnInit, signal } from '@angular/core';
import { TranslatePipe } from '../../services/translate.pipe';

// Пиксельная капибара-питомец, которая гуляет внизу экрана (как vscode-pets).
// Рисунок задан сеткой символов: каждая буква — один пиксель своего цвета, точка — пусто.
const BODY = [
  '................OO......',
  '...............ODDO.....',
  '.....OOOOOOOOOOOBBBOOOO.',
  '...OOBBBBBBBBBBBBBBBBBBO',
  '..OBBBBDBBBBBDBBBBBEBBBO',
  '.OBBBBBBBBBBBBBBBBBBBBBO',
  '.OBBBDBBBBBBDBBBBBBPBBNO',
  'OBBBBBBBBBBBBBBBBBBBBBNO',
  'OBBBBBBBBBBBBBBBBBOOOOO.',
  'OBBBBBBBBBBBBBBBBBO.....',
  'OBBLLLLLLLLLLLLBBBO.....',
  '.OBLLLLLLLLLLLLLBO......',
  '..OOOOOOOOOOOOOOO.......',
];
// два положения ног — из них получается анимация ходьбы
const LEGS_A = ['..ODO.ODO....ODO.ODO....', '..OOO.OOO....OOO.OOO....'];
const LEGS_B = ['...ODO.ODO..ODO.ODO.....', '...OOO.OOO..OOO.OOO.....'];

const COLORS: Record<string, string> = {
  O: '#3b2416', // контур
  B: '#a0673a', // шерсть
  D: '#8a5530', // тёмные пятнышки
  L: '#c48a58', // светлое брюшко
  N: '#4a2c1a', // нос
  E: '#1a1008', // глаз
  P: '#e88a8a', // румянец
};

interface Pixel {
  x: number;
  y: number;
  color: string;
}

function toPixels(rows: string[]): Pixel[] {
  const pixels: Pixel[] = [];
  rows.forEach((row, y) =>
    [...row].forEach((ch, x) => {
      const color = COLORS[ch];
      if (color) pixels.push({ x, y, color });
    }),
  );
  return pixels;
}

const SCALE = 3; // размер одного «пикселя» на экране
const GRID_W = 24;
const GRID_H = BODY.length + LEGS_A.length;
const MESSAGES = ['pet.msg1', 'pet.msg2', 'pet.msg3'];

@Component({
  selector: 'app-capybara-pet',
  imports: [TranslatePipe],
  templateUrl: './capybara-pet.html',
  styleUrl: './capybara-pet.css',
})
export class CapybaraPet implements OnInit, OnDestroy {
  protected readonly frames = [toPixels([...BODY, ...LEGS_A]), toPixels([...BODY, ...LEGS_B])];
  protected readonly width = GRID_W * SCALE;
  protected readonly height = GRID_H * SCALE;
  protected readonly viewBox = `0 0 ${GRID_W} ${GRID_H}`;

  protected x = signal(24); // позиция слева, px
  protected direction = signal<1 | -1>(1); // 1 — идёт вправо, -1 — влево
  protected frame = signal(0); // 0 или 1 — какие ноги рисовать
  protected message = signal(''); // ключ перевода фразы в облачке
  protected bubbleOnRight = signal(false); // облачко прижать к правому краю, если капибара справа

  private ticks = 0;
  private pauseTicks = 0; // сколько шагов ещё стоять на месте
  private timer?: ReturnType<typeof setInterval>;
  private messageTimer?: ReturnType<typeof setTimeout>;

  ngOnInit(): void {
    const reduceMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
    if (reduceMotion) {
      // пользователь отключил анимации в системе — капибара просто сидит в углу
      this.x.set(window.innerWidth - this.width - 24);
      return;
    }
    this.timer = setInterval(() => this.step(), 90);
  }

  ngOnDestroy(): void {
    clearInterval(this.timer);
    clearTimeout(this.messageTimer);
  }

  // клик по капибаре: она останавливается и говорит фразу
  pet(): void {
    const next = MESSAGES[Math.floor(Math.random() * MESSAGES.length)];
    this.message.set(next);
    this.pauseTicks = 30;
    this.frame.set(0);
    clearTimeout(this.messageTimer);
    this.messageTimer = setTimeout(() => this.message.set(''), 2500);
  }

  private step(): void {
    this.bubbleOnRight.set(this.x() > window.innerWidth / 2);

    if (this.pauseTicks > 0) {
      this.pauseTicks--;
      return;
    }
    // иногда капибара останавливается отдохнуть
    if (Math.random() < 0.008) {
      this.pauseTicks = 20 + Math.floor(Math.random() * 40);
      this.frame.set(0);
      return;
    }

    const maxX = window.innerWidth - this.width - 8;
    let next = this.x() + this.direction() * 2;
    if (next >= maxX) {
      next = maxX;
      this.direction.set(-1);
    } else if (next <= 8) {
      next = 8;
      this.direction.set(1);
    }
    this.x.set(next);

    // ноги переставляются каждые 3 шага
    this.ticks++;
    if (this.ticks % 3 === 0) this.frame.update((f) => (f === 0 ? 1 : 0));
  }
}
