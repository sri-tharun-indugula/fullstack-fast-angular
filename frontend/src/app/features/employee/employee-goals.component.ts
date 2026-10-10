import { Component, inject, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';

import { GoalStatus, PerformanceGoal } from '../../core/models/goal.models';
import { GoalService } from '../../core/services/goal.service';

@Component({
  selector: 'app-employee-goals',
  imports: [MatFormFieldModule, MatInputModule, MatSelectModule, MatButtonModule],
  template: `
    <h1>My goals</h1>
    @if (goals().length === 0) {
      <p>No goals assigned yet.</p>
    }
    @for (goal of goals(); track goal.id) {
      <article class="goal">
        <h2>{{ goal.title }}</h2>
        <p>{{ goal.description }}</p>
        <p class="meta">Due: {{ goal.due_date ?? '—' }} · Status: {{ goal.status }}</p>
        @if (goal.manager_note) {
          <p class="note">Manager note: {{ goal.manager_note }}</p>
        }
        <div class="row">
          <mat-form-field appearance="outline">
            <mat-label>Progress %</mat-label>
            <input
              matInput
              type="number"
              min="0"
              max="100"
              [value]="goal.progress_percent"
              (change)="onProgressChange(goal, $event)"
            />
          </mat-form-field>
          <mat-form-field appearance="outline">
            <mat-label>Status</mat-label>
            <mat-select [value]="goal.status" (selectionChange)="onStatusChange(goal, $event.value)">
              <mat-option value="not_started">Not started</mat-option>
              <mat-option value="in_progress">In progress</mat-option>
              <mat-option value="completed">Completed</mat-option>
            </mat-select>
          </mat-form-field>
        </div>
      </article>
    }
  `,
  styles: `
    .goal {
      border: 1px solid var(--mat-sys-outline-variant);
      border-radius: 8px;
      padding: 1rem;
      margin-bottom: 1rem;
    }
    .meta {
      color: var(--mat-sys-on-surface-variant);
    }
    .note {
      font-style: italic;
    }
    .row {
      display: flex;
      gap: 1rem;
      flex-wrap: wrap;
    }
    mat-form-field {
      min-width: 10rem;
    }
  `,
})
export class EmployeeGoalsComponent {
  private readonly goalsApi = inject(GoalService);

  readonly goals = signal<PerformanceGoal[]>([]);

  constructor() {
    this.reload();
  }

  reload(): void {
    this.goalsApi.mine().subscribe({ next: (items) => this.goals.set(items) });
  }

  onProgressChange(goal: PerformanceGoal, event: Event): void {
    const value = Number((event.target as HTMLInputElement).value);
    this.save(goal.id, { progress_percent: value });
  }

  onStatusChange(goal: PerformanceGoal, status: GoalStatus): void {
    this.save(goal.id, { status });
  }

  private save(goalId: string, body: { progress_percent?: number; status?: GoalStatus }): void {
    this.goalsApi.updateSelf(goalId, body).subscribe({ next: () => this.reload() });
  }
}
