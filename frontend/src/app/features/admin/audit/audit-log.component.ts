import { Component, OnInit, signal } from "@angular/core";
import { CommonModule } from "@angular/common";
import { AuditService, SecurityAuditLog } from "../../../core/services/audit.service";

@Component({
  selector: "app-audit-log",
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="audit-log space-y-6">
      <!-- Header -->
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
        <div>
          <h1 class="text-xl font-bold text-slate-800">دفتر ثبت رخدادهای امنیتی (Audit Trail)</h1>
          <p class="text-xs text-slate-500 mt-1">گزارش تغییرناپذیر ثبت رخدادهای دسترسی، احراز هویت و تغییرات سطوح دسترسی کاتالوگ.</p>
        </div>
        <button
          (click)="loadLogs()"
          [disabled]="loading()"
          class="inline-flex items-center gap-2 px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg transition-colors cursor-pointer disabled:opacity-50"
        >
          <i class="pi pi-refresh text-xs" [ngClass]="{ 'pi-spin': loading() }"></i>
          <span>بروزرسانی لاگها</span>
        </button>
      </div>

      <!-- Logs Table Card -->
      <div class="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div *ngIf="loading()" class="p-8 text-center text-slate-500 text-xs">
          <i class="pi pi-spin pi-spinner text-2xl text-blue-600 mb-2"></i>
          <div>در حال دریافت و بارگذاری رخدادهای امنیتی...</div>
        </div>

        <div *ngIf="errorMessage()" class="p-4 bg-rose-50 border-b border-rose-200 text-rose-700 text-xs">
          {{ errorMessage() }}
        </div>

        <div *ngIf="!loading() && logs().length === 0" class="p-12 text-center text-slate-400">
          <i class="pi pi-history text-4xl mb-2 text-slate-300"></i>
          <div class="text-sm font-semibold text-slate-600">هیچ رخداد امنیتی ثبت نشده است</div>
          <div class="text-xs text-slate-400 mt-1">رخدادهای مربوط به ورود، ایجاد کاربران و نقشها در اینجا ثبت میشوند.</div>
        </div>

        <div *ngIf="!loading() && logs().length > 0" class="overflow-x-auto">
          <table class="w-full text-start text-xs">
            <thead class="bg-slate-50 text-slate-600 border-b border-slate-200 font-semibold">
              <tr>
                <th class="px-6 py-3.5 text-start">زمان رخداد</th>
                <th class="px-6 py-3.5 text-start">نوع رخداد</th>
                <th class="px-6 py-3.5 text-start">وضعیت</th>
                <th class="px-6 py-3.5 text-start">منبع / هدف</th>
                <th class="px-6 py-3.5 text-start">آدرس آیپی</th>
                <th class="px-6 py-3.5 text-start">جزئیات</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100 font-mono text-[11px]">
              <tr *ngFor="let log of logs()" class="hover:bg-slate-50/70 transition-colors">
                <td class="px-6 py-3.5 text-slate-500 whitespace-nowrap dir-ltr text-end">
                  {{ formatDate(log.timestamp) }}
                </td>
                <td class="px-6 py-3.5">
                  <span
                    class="px-2 py-0.5 rounded font-semibold text-[10px]"
                    [ngClass]="getEventBadgeClass(log.event_type)"
                  >
                    {{ getEventTitle(log.event_type) }}
                  </span>
                </td>
                <td class="px-6 py-3.5">
                  <span
                    class="px-2 py-0.5 rounded text-[10px] font-semibold"
                    [ngClass]="log.status === 'SUCCESS' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-rose-50 text-rose-700 border border-rose-200'"
                  >
                    {{ log.status === 'SUCCESS' ? 'موفق' : 'ناموفق' }}
                  </span>
                </td>
                <td class="px-6 py-3.5 text-slate-800 font-medium">
                  {{ log.target_resource || '—' }}
                </td>
                <td class="px-6 py-3.5 text-slate-500 dir-ltr text-end">
                  {{ log.ip_address || '—' }}
                </td>
                <td class="px-6 py-3.5 text-slate-400 font-sans max-w-xs truncate">
                  {{ formatDetails(log.details) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  `,
})
export class AuditLogComponent implements OnInit {
  logs = signal<SecurityAuditLog[]>([]);
  loading = signal(true);
  errorMessage = signal<string | null>(null);

  constructor(private auditService: AuditService) {}

  ngOnInit(): void {
    this.loadLogs();
  }

  loadLogs(): void {
    this.loading.set(true);
    this.errorMessage.set(null);

    this.auditService.getAuditLogs().subscribe({
      next: (data) => {
        this.logs.set(data);
        this.loading.set(false);
      },
      error: (err: { error?: { detail?: string } }) => {
        this.errorMessage.set(err.error?.detail || "خطا در دریافت لاگهای امنیتی.");
        this.loading.set(false);
      },
    });
  }

  formatDate(ts: string): string {
    try {
      const d = new Date(ts);
      return d.toLocaleString("fa-IR");
    } catch {
      return ts;
    }
  }

  formatDetails(details: Record<string, unknown> | null): string {
    if (!details || Object.keys(details).length === 0) return "—";
    return JSON.stringify(details);
  }

  getEventTitle(eventType: string): string {
    const titles: Record<string, string> = {
      LOGIN_SUCCESS: "ورود موفق به سامانه",
      LOGIN_FAILED: "تلاش ورود ناموفق",
      USER_CREATED: "تعریف کاربر جدید",
      ROLE_CREATED: "تعریف نقش سفارشی",
      PASSWORD_CHANGE: "تغییر کلمه عبور",
      SESSION_REVOKED: "ابطال نشست فعال",
      ACCOUNT_LOCKED: "قفل موقت حساب کاربری",
    };
    return titles[eventType] || eventType;
  }

  getEventBadgeClass(eventType: string): string {
    if (eventType.includes("SUCCESS")) {
      return "bg-emerald-50 text-emerald-700 border border-emerald-200";
    }
    if (eventType.includes("FAILED") || eventType.includes("LOCKED")) {
      return "bg-rose-50 text-rose-700 border border-rose-200";
    }
    if (eventType.includes("USER_") || eventType.includes("ROLE_")) {
      return "bg-blue-50 text-blue-700 border border-blue-200";
    }
    return "bg-slate-100 text-slate-700 border border-slate-200";
  }
}
