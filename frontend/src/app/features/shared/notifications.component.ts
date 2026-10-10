import { Component, inject, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';

import { AppNotification } from '../../core/models/notification.models';
import { NotificationService } from '../../core/services/notification.service';

@Component({
  selector: 'app-notifications',
  imports: [MatButtonModule],
  template: `
    <h1>Notifications</h1>
    <button mat-button type="button" (click)="markAllRead()" [disabled]="items().length === 0">Mark all read</button>
    @if (items().length === 0) {
      <p>No notifications.</p>
    }
    @for (item of items(); track item.id) {
      <article class="item" [class.unread]="!item.read_at">
        <h2>{{ item.title }}</h2>
        <p>{{ item.body }}</p>
        <p class="meta">{{ item.created_at }} · {{ item.kind }}</p>
        @if (!item.read_at) {
          <button mat-button type="button" (click)="markRead(item)">Mark read</button>
        }
      </article>
    }
  `,
  styles: `
    .item {
      border: 1px solid var(--mat-sys-outline-variant);
      border-radius: 8px;
      padding: 1rem;
      margin: 1rem 0;
    }
    .item.unread {
      border-color: var(--mat-sys-primary);
    }
    .meta {
      color: var(--mat-sys-on-surface-variant);
      font-size: 0.875rem;
    }
  `,
})
export class NotificationsComponent {
  private readonly api = inject(NotificationService);

  readonly items = signal<AppNotification[]>([]);

  constructor() {
    this.reload();
  }

  reload(): void {
    this.api.mine().subscribe({
      next: (list) => this.items.set(list),
    });
  }

  markRead(item: AppNotification): void {
    this.api.markRead(item.id).subscribe({
      next: (updated) => {
        this.items.update((rows) => rows.map((row) => (row.id === updated.id ? updated : row)));
      },
    });
  }

  markAllRead(): void {
    this.api.markAllRead().subscribe({
      next: () => this.reload(),
    });
  }
}
