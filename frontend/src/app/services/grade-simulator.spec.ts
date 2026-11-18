import { calcTotal, neededFinal, simulate, targetHints } from './grade-simulator';

// Автотесты логики симулятора. Запуск: cd frontend && npx ng test
describe('Grade simulator', () => {
  describe('Mode 1: total = 0.6 × Midterm + 0.4 × Final', () => {
    it('80 and 95 give 86% (B+), scholarship is safe', () => {
      const r = simulate(80, 95);
      expect(r.total).toBe(86);
      expect(r.letter).toBe('B+');
      expect(r.zone).toBe('ok');
    });

    it('80 and 50 give 68% — red zone, risk of losing the scholarship', () => {
      const r = simulate(80, 50);
      expect(r.total).toBe(68);
      expect(r.zone).toBe('risk');
      expect(r.statusKey).toBe('sim.status.risk');
    });

    it('exactly 70% keeps the scholarship', () => {
      expect(simulate(80, 55).zone).toBe('ok');
    });

    it('90% is the increased scholarship level (A-, GPA 3.67)', () => {
      const r = simulate(90, 90);
      expect(r.letter).toBe('A-');
      expect(r.gpa).toBe(3.67);
      expect(r.zone).toBe('high');
    });

    it('below 50% the course is failed (F)', () => {
      const r = simulate(40, 40);
      expect(r.letter).toBe('F');
      expect(r.zone).toBe('fail');
    });

    it('scores outside 0–100 are clamped', () => {
      expect(calcTotal(150, 100)).toBe(100);
      expect(calcTotal(-20, 100)).toBe(40);
    });

    it('uses custom course weights', () => {
      expect(calcTotal(60, 80, { midterm: 0.5, final: 0.5 })).toBe(70);
    });
  });

  describe('Mode 2: Final needed for a goal', () => {
    it('with midterm 80, at least 55 is needed for 70%', () => {
      expect(neededFinal(80, 70)).toBe(55);
    });

    it('with midterm 80, 90% is out of reach', () => {
      expect(neededFinal(80, 90)).toBeNull();
    });

    it('with midterm 95, at least 83 is needed for 90%', () => {
      expect(neededFinal(95, 90)).toBe(83);
      expect(calcTotal(95, 83)).toBeGreaterThanOrEqual(90);
      expect(calcTotal(95, 82)).toBeLessThan(90);
    });

    it('returns 0 when the goal is already guaranteed', () => {
      expect(neededFinal(100, 60)).toBe(0);
    });

    it('builds both hints with translation keys and params', () => {
      const [h70, h90] = targetHints(80);
      expect(h70.messageKey).toBe('sim.target70.need');
      expect(h70.params).toEqual({ goal: 70, score: 55 });
      expect(h90.messageKey).toBe('sim.target90.impossible');
    });
  });
});
