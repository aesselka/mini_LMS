import { Injectable } from '@angular/core';
import {
  DEFAULT_WEIGHTS,
  INCREASED_THRESHOLD,
  SCHOLARSHIP_THRESHOLD,
  SimulationResult,
  TargetHint,
  Weights,
  calcTotal,
  neededFinal,
  simulate,
  targetHints,
} from './grade-simulator';

// Сервис симулятора оценок для страниц (виджет в дашборде студента делает Участник 4).
//
// Пример в компоненте — пересчёт «на лету» при движении ползунка:
//   private sim = inject(GradeSimulatorService);
//   midterm = signal(80);          // current_midterm_avg из GET /api/courses/my-standing/
//   expectedFinal = signal(95);    // значение ползунка 0–100
//   result = computed(() => this.sim.simulate(this.midterm(), this.expectedFinal()));
//   hints  = computed(() => this.sim.targets(this.midterm()));
// В шаблоне:
//   {{ result().total }}% ({{ result().letter }})  ·  {{ result().statusKey | t }}
//   @for (h of hints(); track h.goal) { <p>{{ h.messageKey | t: h.params }}</p> }
//   [class]="'zone-' + result().zone"   // high / ok / risk / fail — для цвета
@Injectable({ providedIn: 'root' })
export class GradeSimulatorService {
  readonly scholarshipThreshold = SCHOLARSHIP_THRESHOLD; // 70
  readonly increasedThreshold = INCREASED_THRESHOLD; // 90
  readonly defaultWeights = DEFAULT_WEIGHTS; // 0.6 / 0.4

  // Режим 1: итог, буква, баллы GPA, зона и текст статуса
  simulate(midterm: number, expectedFinal: number, weights: Weights = DEFAULT_WEIGHTS): SimulationResult {
    return simulate(midterm, expectedFinal, weights);
  }

  total(midterm: number, expectedFinal: number, weights: Weights = DEFAULT_WEIGHTS): number {
    return calcTotal(midterm, expectedFinal, weights);
  }

  // Режим 2: сколько нужно на Final для цели (null — недостижимо, 0 — уже гарантировано)
  neededFinal(midterm: number, goal: number, weights: Weights = DEFAULT_WEIGHTS): number | null {
    return neededFinal(midterm, goal, weights);
  }

  // Подсказки «сколько нужно на Final» для 70% и 90%
  targets(midterm: number, weights: Weights = DEFAULT_WEIGHTS): TargetHint[] {
    return targetHints(midterm, weights);
  }
}
