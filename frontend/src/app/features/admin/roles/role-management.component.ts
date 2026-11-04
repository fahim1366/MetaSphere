import { Component, OnInit, signal } from "@angular/core";
import { CommonModule } from "@angular/common";
import { RoleService, Permission } from "../../../core/services/role.service";
import { Role } from "../../../core/models/user.model";

@Component({
  selector: "app-role-management",
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="role-management space-y-6">
      <!-- Header -->
      <div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
        <h1 class="text-xl font-bold text-slate-800">Role & Permission Matrix</h1>
        <p class="text-xs text-slate-500 mt-1">
          Inspect built-in governance roles, system capabilities, and server-enforced access policies.
        </p>
      </div>

      <!-- Loading State -->
      <div *ngIf="loading()" class="p-8 text-center text-slate-500 text-xs bg-white rounded-xl border border-slate-200">
        <i class="pi pi-spin pi-spinner text-2xl text-blue-600 mb-2"></i>
        <div>Loading roles and permission capabilities...</div>
      </div>

      <!-- Roles Grid -->
      <div *ngIf="!loading()" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div
          *ngFor="let role of roles()"
          class="bg-white rounded-xl border border-slate-200 shadow-sm p-6 flex flex-col justify-between hover:border-slate-300 transition-colors"
        >
          <div>
            <div class="flex items-start justify-between gap-2 mb-3">
              <div>
                <h3 class="font-bold text-slate-800 text-sm">{{ role.name }}</h3>
                <div class="font-mono text-[11px] text-blue-600 font-semibold">{{ role.code }}</div>
              </div>
              <span
                class="px-2 py-0.5 rounded text-[10px] font-semibold"
                [ngClass]="role.is_system ? 'bg-purple-50 text-purple-700 border border-purple-200' : 'bg-emerald-50 text-emerald-700 border border-emerald-200'"
              >
                {{ role.is_system ? 'System' : 'Custom' }}
              </span>
            </div>

            <p class="text-xs text-slate-500 mb-4">{{ role.description || 'No description provided.' }}</p>

            <div>
              <div class="text-[11px] font-semibold text-slate-700 mb-2 flex items-center justify-between">
                <span>Associated Permissions</span>
                <span class="text-slate-400 font-normal">({{ role.permissions.length }})</span>
              </div>
              <div class="flex flex-wrap gap-1.5 max-h-36 overflow-y-auto">
                <span
                  *ngFor="let perm of role.permissions"
                  class="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-50 text-slate-700 border border-slate-200"
                >
                  {{ perm }}
                </span>
                <span *ngIf="role.permissions.length === 0" class="text-slate-400 italic text-[11px]">
                  No direct permissions assigned.
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Capability Modules Explorer -->
      <div *ngIf="!loading() && permissions().length > 0" class="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
        <div class="mb-4">
          <h2 class="text-sm font-bold text-slate-800">All System Permissions Directory</h2>
          <p class="text-xs text-slate-500 mt-0.5">Granular action permissions verified by FastAPI dependencies.</p>
        </div>

        <div class="overflow-x-auto">
          <table class="w-full text-start text-xs">
            <thead class="bg-slate-50 text-slate-600 border-b border-slate-200 uppercase tracking-wider font-semibold">
              <tr>
                <th class="px-4 py-3 text-start">Module</th>
                <th class="px-4 py-3 text-start">Permission Code</th>
                <th class="px-4 py-3 text-start">Name</th>
                <th class="px-4 py-3 text-start">Description</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr *ngFor="let p of permissions()" class="hover:bg-slate-50/70">
                <td class="px-4 py-3 font-semibold text-blue-600 uppercase text-[10px]">{{ p.module }}</td>
                <td class="px-4 py-3 font-mono font-medium text-slate-800">{{ p.code }}</td>
                <td class="px-4 py-3 text-slate-700">{{ p.name }}</td>
                <td class="px-4 py-3 text-slate-400">{{ p.description || '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  `,
})
export class RoleManagementComponent implements OnInit {
  roles = signal<Role[]>([]);
  permissions = signal<Permission[]>([]);
  loading = signal(true);

  constructor(private roleService: RoleService) {}

  ngOnInit(): void {
    this.roleService.getRoles().subscribe({
      next: (data) => {
        this.roles.set(data);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });

    this.roleService.getPermissions().subscribe({
      next: (data) => this.permissions.set(data),
      error: () => {},
    });
  }
}
