import { Component, computed, input } from '@angular/core';
import { TranslatePipe } from '../../services/translate.pipe';

export type StrengthLevel = 0 | 1 | 2 | 3; // 0 — пусто, 1 — слабый, 2 — средний, 3 — надёжный

// Оценка надёжности пароля: за каждое выполненное правило +1 балл.
export function passwordScore(password: string): number {
  if (!password) return 0;
  let score = 0;
  if (password.length >= 8) score++;
  if (password.length >= 12) score++;
  if (/[a-zа-яё]/.test(password) && /[A-ZА-ЯЁ]/.test(password)) score++; // строчные и заглавные
  if (/\d/.test(password)) score++; // цифры
  if (/[^A-Za-zА-Яа-яЁё0-9]/.test(password)) score++; // символы: !@#$%...
  if (/^\d+$/.test(password) || password.length < 8) score = Math.min(score, 1); // только цифры или коротко — всегда слабый
  return score; // 0..5
}

export function strengthLevel(password: string): StrengthLevel {
  if (!password) return 0;
  const score = passwordScore(password);
  if (score <= 2) return 1;
  if (score === 3) return 2;
  return 3;
}

@Component({
  selector: 'app-password-strength',
  imports: [TranslatePipe],
  templateUrl: './password-strength.html',
  styleUrl: './password-strength.css',
})
export class PasswordStrength {
  readonly password = input('');

  protected level = computed(() => strengthLevel(this.password()));
  protected labelKey = computed(() => ['', 'strength.weak', 'strength.medium', 'strength.strong'][this.level()]);

  // подсказки: какие правила ещё не выполнены
  protected hints = computed(() => {
    const p = this.password();
    const list: string[] = [];
    if (p.length < 12) list.push('strength.hintLength');
    if (!(/[a-zа-яё]/.test(p) && /[A-ZА-ЯЁ]/.test(p))) list.push('strength.hintCase');
    if (!/\d/.test(p)) list.push('strength.hintDigit');
    if (!/[^A-Za-zА-Яа-яЁё0-9]/.test(p)) list.push('strength.hintSymbol');
    return list;
  });
}
