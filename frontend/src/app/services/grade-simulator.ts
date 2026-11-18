// Логика симулятора оценок «Что если?» (Участник 2).
// Чистые функции без Angular: их легко тестировать и использовать где угодно.
//
// Формула: Total = midtermWeight × Midterm + finalWeight × Final  (по умолчанию 0.6 и 0.4)
// Пороги:  70% — стипендия, 90% — повышенная стипендия (A-, GPA 3.67+), ниже 50% — курс не сдан.

export interface Weights {
  midterm: number; // доля Midterm + Endterm, например 0.6
  final: number; // доля Final, например 0.4
}

export const DEFAULT_WEIGHTS: Weights = { midterm: 0.6, final: 0.4 };

export const SCHOLARSHIP_THRESHOLD = 70;
export const INCREASED_THRESHOLD = 90;
export const PASS_THRESHOLD = 50;

// Зона для цвета виджета: high — повышенная (90+), ok — стипендия (70–89), risk — красная зона (50–69), fail — не сдан (<50)
export type Zone = 'high' | 'ok' | 'risk' | 'fail';

// Шкала букв — такая же, как GRADE_POINTS в backend/courses/models.py
const LETTER_SCALE: { min: number; letter: string; points: number }[] = [
  { min: 95, letter: 'A', points: 4.0 },
  { min: 90, letter: 'A-', points: 3.67 },
  { min: 85, letter: 'B+', points: 3.33 },
  { min: 80, letter: 'B', points: 3.0 },
  { min: 75, letter: 'B-', points: 2.67 },
  { min: 70, letter: 'C+', points: 2.33 },
  { min: 65, letter: 'C', points: 2.0 },
  { min: 60, letter: 'C-', points: 1.67 },
  { min: 55, letter: 'D+', points: 1.33 },
  { min: 50, letter: 'D', points: 1.0 },
  { min: 0, letter: 'F', points: 0.0 },
];

export interface SimulationResult {
  total: number; // итог в процентах, округлён до 0.1
  letter: string; // A, A-, B+ ...
  gpa: number; // баллы GPA за букву
  zone: Zone;
  statusKey: string; // ключ перевода статуса, например 'sim.status.risk'
}

export interface TargetHint {
  goal: number; // 70 или 90
  needed: number | null; // минимальный балл за Final; null — уже недостижимо
  messageKey: string; // ключ перевода подсказки
  params: Record<string, number>; // параметры для перевода: {goal}, {score}
}

// Оценка всегда в пределах 0–100; всё, что не число, считается 0
export function clampScore(value: number): number {
  if (!Number.isFinite(value)) return 0;
  return Math.min(100, Math.max(0, value));
}

function round1(value: number): number {
  return Math.round(value * 10) / 10;
}

// Режим 1: итоговый балл по формуле
export function calcTotal(midterm: number, final: number, weights: Weights = DEFAULT_WEIGHTS): number {
  return round1(weights.midterm * clampScore(midterm) + weights.final * clampScore(final));
}

export function letterFor(total: number): { letter: string; points: number } {
  const row = LETTER_SCALE.find((r) => total >= r.min) ?? LETTER_SCALE[LETTER_SCALE.length - 1];
  return { letter: row.letter, points: row.points };
}

export function zoneFor(total: number): Zone {
  if (total >= INCREASED_THRESHOLD) return 'high';
  if (total >= SCHOLARSHIP_THRESHOLD) return 'ok';
  if (total >= PASS_THRESHOLD) return 'risk';
  return 'fail';
}

const STATUS_KEYS: Record<Zone, string> = {
  high: 'sim.status.high',
  ok: 'sim.status.ok',
  risk: 'sim.status.risk',
  fail: 'sim.status.fail',
};

export function simulate(midterm: number, final: number, weights: Weights = DEFAULT_WEIGHTS): SimulationResult {
  const total = calcTotal(midterm, final, weights);
  const { letter, points } = letterFor(total);
  const zone = zoneFor(total);
  return { total, letter, gpa: points, zone, statusKey: STATUS_KEYS[zone] };
}

// Режим 2: сколько минимум нужно на Final, чтобы итог был не меньше goal.
// 0 — цель уже гарантирована при любом Final; null — недостижимо даже со 100 на Final.
export function neededFinal(midterm: number, goal: number, weights: Weights = DEFAULT_WEIGHTS): number | null {
  if (weights.final <= 0) return weights.midterm * clampScore(midterm) >= goal ? 0 : null;
  // маленький допуск, чтобы 0.6·80 + 0.4·55 = 70 не превратилось в 55.0000001 → 56
  const raw = (goal - weights.midterm * clampScore(midterm)) / weights.final - 1e-9;
  const needed = Math.max(0, Math.ceil(raw));
  return needed > 100 ? null : needed;
}

// Подсказки под ползунком: для стипендии (70%) и повышенной стипендии (90%)
export function targetHints(midterm: number, weights: Weights = DEFAULT_WEIGHTS): TargetHint[] {
    return [SCHOLARSHIP_THRESHOLD, INCREASED_THRESHOLD].map((goal): TargetHint => {
    const needed = neededFinal(midterm, goal, weights);
    const prefix = goal === SCHOLARSHIP_THRESHOLD ? 'sim.target70' : 'sim.target90';
    if (needed === null) return { goal, needed, messageKey: `${prefix}.impossible`, params: { goal } };
    if (needed === 0) return { goal, needed, messageKey: `${prefix}.done`, params: { goal } };
    return { goal, needed, messageKey: `${prefix}.need`, params: { goal, score: needed } };
  });
}
