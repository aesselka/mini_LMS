import { Component, OnInit, computed, inject } from '@angular/core';
import { AvatarView } from '../../components/avatar/avatar';
import { Achievement, AchievementsService } from '../../services/achievements.service';
import { Avatar } from '../../services/preferences.service';
import { TranslatePipe } from '../../services/translate.pipe';

// Страница «Достижения»: значки, прогресс и подбадривание от капибары
@Component({
  selector: 'app-achievements',
  imports: [TranslatePipe, AvatarView],
  templateUrl: './achievements.html',
  styleUrl: './achievements.css',
})
export class Achievements implements OnInit {
  protected ach = inject(AchievementsService);
  protected readonly capy: Avatar = { kind: 'preset', color: 'golden' };

  // сначала полученные, потом ближайшие к получению
  protected sorted = computed(() =>
    [...this.ach.achievements()].sort((a, b) => Number(b.unlocked) - Number(a.unlocked) || b.percent - a.percent),
  );

  protected total = computed(() => this.ach.achievements().length);
  protected overall = computed(() => Math.round((this.ach.unlockedCount() / Math.max(1, this.total())) * 100));

  // фраза капибары зависит от прогресса
  protected capyLine = computed(() => {
    const p = this.overall();
    if (p === 100) return 'ach.capy.all';
    if (p >= 50) return 'ach.capy.half';
    if (p > 0) return 'ach.capy.start';
    return 'ach.capy.zero';
  });

  ngOnInit(): void {
    this.ach.refresh(true);
  }

  format(a: Achievement, v: number): string {
    return a.decimals ? v.toFixed(a.decimals) : String(Math.floor(v));
  }
}
