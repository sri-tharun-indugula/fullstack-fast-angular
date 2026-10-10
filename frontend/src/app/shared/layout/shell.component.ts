import { Component, inject, signal } from '@angular/core';
import { Router, RouterLink, RouterOutlet } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatToolbarModule } from '@angular/material/toolbar';

import { AuthService } from '../../core/auth/auth.service';
import { NotificationService } from '../../core/services/notification.service';

@Component({
  selector: 'app-shell',
  imports: [RouterOutlet, RouterLink, MatToolbarModule, MatButtonModule],
  templateUrl: './shell.component.html',
  styleUrl: './shell.component.scss',
})
export class ShellComponent {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  private readonly notifications = inject(NotificationService);

  readonly user = this.auth.user;
  readonly unreadCount = signal(0);

  constructor() {
    this.notifications.unreadCount().subscribe({
      next: (payload) => this.unreadCount.set(payload.count),
    });
  }

  logout(): void {
    this.auth.logout().subscribe({
      next: () => {
        void this.router.navigateByUrl('/login');
      },
    });
  }
}
