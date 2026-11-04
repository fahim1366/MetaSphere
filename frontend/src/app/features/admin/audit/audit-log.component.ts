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
          <h1 class="text-xl font-bold text-slate-800">Security Audit Trail</h1>
          <p class="text-xs text-slate-500 mt-1">Immutable security and access event logs recorded across the enterprise catalog.</p>
        </div>
        <button
          (click)="loadLogs()"
          [disabled]="loading()"
          class="inline-flex items-center gap-2 px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg transition-colors cursor-pointer disabled:opacity-50"
        >
          <i class="pi pi-refresh text-xs" [ngClass]="{ 'pi-spin': loading() }"></i>
          <span>Refresh Logs</span>
        </button>
      </div>

      <!-- Logs Table Card -->
      <div class="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div *ngIf="loading()" class="p-8 text-center text-slate-500 text-xs">
          <i class="pi pi-spin pi-spinner text-2xl text-blue-600 mb-2"></i>
          <div>Loading security audit events...</div>
        </div>

        <div *ngIf="errorMessage()" class="p-4 bg-rose-50 border-b border-rose-200 text-rose-700 text-xs">
          {{ errorMessage() }}
        </div>

        <div *ngIf="!loading() && logs().length === 0" class="p-12 text-center text-slate-400">
          <i class="pi pi-history text-4xl mb-2 text-slate-300"></i>
          <div class="text-sm font-semibold text-slate-600">No audit events recorded yet</div>
          <div class="text-xs text-slate-400 mt-1">Security-relevant operations will be automatically journaled here.</div>
        </div>

        <div *ngIf="!loading() && logs().length > 0" class="overflow-x-auto">
          <table class="w-full text-start text-xs">
            <thead class="bg-slate-50 text-slate-600 border-b border-slate-200 uppercase tracking-wider font-semibold">
              <tr>
                <th class="px-6 py-3.5 text-start">Timestamp</th>
                <th class="px-6 py-3.5 text-start">Event Type</th>
                <th class="px-6 py-3.5 text-start">Status</th>
                <th class="px-6 py-3.5 text-start">Target Resource</th>
                <th class="px-6 py-3.5 text-start">IP Address</th>
                <th class="px-6 py-3.5 text-start">Details</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100 font-mono text-[11px]">
              <tr *ngFor="let log of logs()" class="hover:bg-slate-50/70 transition-colors">
                <td class="px-6 py-3.5 text-slate-500 whitespace-nowrap">
                  {{ formatDate(log.timestamp) }}
                </td>
                <td class="px-6 py-3.5">
                  <span
                    class="px-2 py-0.5 rounded font-semibold text-[10px]"
                    [ngClass]="getEventBadgeClass(log.event_type)"
                  >
                    {{ log.event_type }}
                  </span>
                </td>
                <td class="px-6 py-3.5">
                  <span
                    class="px-2 py-0.5 rounded text-[10px] font-semibold uppercase"
                    [ngClass]="log.status === 'SUCCESS' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-rose-50 text-rose-700 border border-rose-200'"
                  >
                    {{ log.status }}
                  </span>
                </td>
                <td class="px-6 py-3.5 text-slate-800 font-medium">
                  {{ log.target_resource || '—' }}
                </td>
                <td class="px-6 py-3.5 text-slate-500">
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
        this.errorMessage.set(err.error?.detail || "Failed to load audit logs.");
        this.loading.set(false);
      },
    });
  }

  formatDate(ts: string): string {
    try {
      const d = new Date(ts);
      return d.toLocaleString();
    } catch {
      return ts;
    }
  }

  formatDetails(details: Record<string, unknown> | null): string {
    if (!details || Object.keys(details).length === 0) return "—";
    return JSON.stringify(details);
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
