import { Component, OnDestroy, OnInit, inject, signal } from '@angular/core';
import { TranslatePipe } from '../../services/translate.pipe';
import { PreferencesService } from '../../services/preferences.service';

// Пиксельная капибара-питомец (как vscode-pets).
// • Гуляет по всему периметру окна: по низу, по правой стене, вверх ногами по верху, по левой стене.
// • Её можно взять мышкой / пальцем и перенести — после отпускания она прилипает к ближайшему краю.
// • Клик — говорит фразу.
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

// картинка «в руках»: смотрит на нас и удивляется — носик, глазки с бликом, румянец, лапки у груди
const HELD = [
  '.....OOO........OOO...Y.',
  '....OBBBO......OBBBO.Y..',
  '....OBDBOOOOOOOOBDBO....',
  '....OBBBBBBBBBBBBBBO....',
  '....OBBBBBBBBBBBBBBO.YYY',
  '...OBBBBBBBBBBBBBBBBO...',
  '...OBBBBBBBBBBBBBBBBOYY.',
  '...OBBBWEBBBBBBWEBBBO...',
  '...OBBBEEDDDDDDEEBBBO...',
  '...OBBBBBDNDDNDBBBBBO...',
  '...OBPPBBDDDDDDBBPPBO...',
  '...OBBBBBBNMMNBBBBBBO...',
  '...OBBBBBBNMMNBBBBBBO...',
  '....OBBBBBBNNBBBBBBO....',
  '....OBBBOOBBBBBOOBBO....',
  '....OBBODDOBBBODDOBO....',
  '....OBBODDOLLLODDOBO....',
  '....OBBBOOLLLLLOOBBO....',
  '...OBBBLLLLLLLLLLBBBO...',
  '....OBBLLLLLLLLLLBBO....',
  '...GOBBLLLLLLLLLLBBOG...',
  '...GOBBBLLLLLLLLBBBOG...',
  '....GOBBBLLLLLLBBBOG....',
  '......ODDDBBBBDDDO......',
  '......ODDDOOOODDDO......',
  '.......OOO....OOO.......',
];

const COLORS: Record<string, string> = {
  O: '#3b2416', // контур
  B: '#a0673a', // шерсть
  D: '#8a5530', // тёмные пятнышки
  L: '#c48a58', // светлое брюшко
  N: '#4a2c1a', // нос
  E: '#1a1008', // глаз
  P: '#e88a8a', // румянец
  W: '#ffffff', // блик в глазу
  S: '#3b2416', // нижний край глаза
  M: '#f2738c', // открытый ротик
  Y: '#f59e0b', // чёрточки удивления
  G: '#7c6f66', // линии движения
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
const HELD_SCALE = 2.5; // «в руках» капибара чуть меньше
const GRID_W = 24;
const GRID_H = BODY.length + LEGS_A.length;
const PET_W = GRID_W * SCALE; // 72px — длина капибары
const PET_H = GRID_H * SCALE; // 45px — высота
const SPEED = 3; // px за шаг
const TICK_MS = 80;
const DRAG_THRESHOLD = 5; // px — дальше этого считается перетаскиванием, а не кликом
const MESSAGES = ['pet.msg1', 'pet.msg2', 'pet.msg3'];

type Edge = 'bottom' | 'right' | 'top' | 'left';

// Поворот для каждого края: лапы всегда смотрят к краю экрана
const EDGE_ANGLE: Record<Edge, number> = { bottom: 0, right: -90, top: -180, left: -270 };

@Component({
  selector: 'app-capybara-pet',
  imports: [TranslatePipe],
  templateUrl: './capybara-pet.html',
  styleUrl: './capybara-pet.css',
})
export class CapybaraPet implements OnInit, OnDestroy {
  protected readonly frames = [toPixels([...BODY, ...LEGS_A]), toPixels([...BODY, ...LEGS_B])];
  protected readonly width = PET_W;
  protected readonly height = PET_H;
  protected readonly viewBox = `0 0 ${GRID_W} ${GRID_H}`;
  protected readonly heldPixels = toPixels(HELD);
  protected readonly heldWidth = HELD[0].length * HELD_SCALE; // 60px
  protected readonly heldHeight = HELD.length * HELD_SCALE; // 65px
  protected readonly heldViewBox = `0 0 ${HELD[0].length} ${HELD.length}`;

  // центр капибары на экране и её поворот
  protected cx = signal(PET_W / 2);
  protected cy = signal(0);
  protected angle = signal(0);
  protected edge = signal<Edge>('bottom');
  protected flip = signal(false); // идёт «назад» по периметру — рисунок отражён
  protected frame = signal(0); // 0 или 1 — какие ноги рисовать
  protected dragging = signal(false);
  protected snapping = signal(false); // плавно «прилипает» к краю после отпускания
  protected message = signal(''); // ключ перевода фразы в облачке
  protected bubbleAlign = signal<'start' | 'center' | 'end'>('center');

  private prefs = inject(PreferencesService);

  private s = 0; // пройденное расстояние по периметру, px
  private direction: 1 | -1 = 1; // 1 — против часовой стрелки (низ → право → верх → лево), -1 — обратно
  private ticks = 0;
  private pauseTicks = 0;
  private timer?: ReturnType<typeof setInterval>;
  private messageTimer?: ReturnType<typeof setTimeout>;
  private snapTimer?: ReturnType<typeof setTimeout>;

  // перетаскивание
  private pointerId: number | null = null;
  private startX = 0;
  private startY = 0;
  private offsetX = 0;
  private offsetY = 0;
  private suppressClick = false;

  private readonly onResize = () => this.place();

  ngOnInit(): void {
    this.s = this.segments().a; // старт — правый нижний угол
    this.place();
    window.addEventListener('resize', this.onResize);

    const reduceMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
    if (!reduceMotion) {
      this.timer = setInterval(() => this.step(), TICK_MS);
    }
  }

  ngOnDestroy(): void {
    clearInterval(this.timer);
    clearTimeout(this.messageTimer);
    clearTimeout(this.snapTimer);
    window.removeEventListener('resize', this.onResize);
  }

  // ---------- клик ----------
  onClick(): void {
    if (this.suppressClick) {
      this.suppressClick = false; // это было перетаскивание, а не клик
      return;
    }
    this.say(MESSAGES[Math.floor(Math.random() * MESSAGES.length)]);
    this.pauseTicks = 30;
    this.prefs.countPet(); // для достижения «Друг капибары»
  }

  // ---------- перетаскивание ----------
  onPointerDown(event: PointerEvent): void {
    if (event.button !== 0) return; // только левая кнопка / палец
    this.pointerId = event.pointerId;
    this.startX = event.clientX;
    this.startY = event.clientY;
    this.offsetX = event.clientX - this.cx();
    this.offsetY = event.clientY - this.cy();
    (event.currentTarget as HTMLElement).setPointerCapture(event.pointerId);
  }

  onPointerMove(event: PointerEvent): void {
    if (event.pointerId !== this.pointerId) return;

    if (!this.dragging()) {
      const moved = Math.hypot(event.clientX - this.startX, event.clientY - this.startY);
      if (moved < DRAG_THRESHOLD) return;
      // начали тащить: капибара повисает лицом к нам и пищит
      this.dragging.set(true);
      this.snapping.set(false);
      this.setAngle(0);
      this.say('pet.drag');
    }

    const { W, H } = this.segments();
    this.cx.set(Math.min(W, Math.max(0, event.clientX - this.offsetX)));
    this.cy.set(Math.min(H, Math.max(0, event.clientY - this.offsetY)));
    this.updateBubbleAlign();
  }

  onPointerUp(event: PointerEvent): void {
    if (event.pointerId !== this.pointerId) return;
    this.pointerId = null;
    if (!this.dragging()) return; // не двигали — это обычный клик, его обработает onClick

    this.dragging.set(false);
    this.suppressClick = true;
    this.dropAt(this.cx(), this.cy());
  }

  // ---------- движение по периметру ----------
  private step(): void {
    if (this.dragging()) return;
    if (this.pauseTicks > 0) {
      this.pauseTicks--;
      return;
    }
    // иногда отдыхает, иногда разворачивается
    const r = Math.random();
    if (r < 0.006) {
      this.pauseTicks = 20 + Math.floor(Math.random() * 40);
      this.frame.set(0);
      return;
    }
    if (r < 0.009) this.direction = this.direction === 1 ? -1 : 1;

    this.s += this.direction * SPEED;
    this.place();

    this.ticks++;
    if (this.ticks % 3 === 0) this.frame.update((f) => (f === 0 ? 1 : 0)); // ноги переставляются
  }

  // длины сторон периметра, по которым может идти центр капибары
  private segments() {
    const W = document.documentElement.clientWidth || window.innerWidth;
    const H = document.documentElement.clientHeight || window.innerHeight;
    const a = Math.max(0, W - PET_W); // низ и верх
    const b = Math.max(0, H - PET_W); // правая и левая стены
    return { W, H, a, b, P: 2 * a + 2 * b };
  }

  // переводит пройденное расстояние s в координаты и поворот
  private place(): void {
    const { W, H, a, b, P } = this.segments();
    if (P <= 0) return;
    this.s = ((this.s % P) + P) % P;
    const s = this.s;

    let edge: Edge;
    if (s < a) {
      edge = 'bottom';
      this.cx.set(PET_W / 2 + s);
      this.cy.set(H - PET_H / 2);
    } else if (s < a + b) {
      edge = 'right';
      this.cx.set(W - PET_H / 2);
      this.cy.set(H - PET_W / 2 - (s - a));
    } else if (s < 2 * a + b) {
      edge = 'top';
      this.cx.set(W - PET_W / 2 - (s - a - b));
      this.cy.set(PET_H / 2);
    } else {
      edge = 'left';
      this.cx.set(PET_H / 2);
      this.cy.set(PET_W / 2 + (s - 2 * a - b));
    }

    this.edge.set(edge);
    this.setAngle(EDGE_ANGLE[edge]);
    this.flip.set(this.direction === -1);
    this.updateBubbleAlign();
  }

  // после отпускания — к ближайшему краю
  private dropAt(x: number, y: number): void {
    const { W, H, a, b } = this.segments();
    const clamp = (v: number, max: number) => Math.min(max, Math.max(0, v));
    const distances: Record<Edge, number> = { bottom: H - y, top: y, left: x, right: W - x };
    const nearest = (Object.keys(distances) as Edge[]).reduce((best, e) => (distances[e] < distances[best] ? e : best));

    if (nearest === 'bottom') this.s = clamp(x - PET_W / 2, a);
    else if (nearest === 'right') this.s = a + clamp(H - PET_W / 2 - y, b);
    else if (nearest === 'top') this.s = a + b + clamp(W - PET_W / 2 - x, a);
    else this.s = 2 * a + b + clamp(y - PET_W / 2, b);

    this.snapping.set(true);
    this.place();
    this.say('pet.dropped');
    this.pauseTicks = 25;
    clearTimeout(this.snapTimer);
    this.snapTimer = setTimeout(() => this.snapping.set(false), 400);
  }

  // поворот выбирается ближайшим путём, чтобы на углах капибара не делала лишний оборот
  private setAngle(base: number): void {
    const current = this.angle();
    this.angle.set(base + 360 * Math.round((current - base) / 360));
  }

  private updateBubbleAlign(): void {
    const { W } = this.segments();
    const x = this.cx();
    this.bubbleAlign.set(x < 140 ? 'start' : x > W - 140 ? 'end' : 'center');
  }

  private say(key: string): void {
    this.message.set(key);
    clearTimeout(this.messageTimer);
    this.messageTimer = setTimeout(() => this.message.set(''), 2500);
  }

  // где показывать облачко: всегда внутрь экрана от края
  protected bubbleSide(): Edge {
    return this.dragging() ? 'bottom' : this.edge();
  }
}
