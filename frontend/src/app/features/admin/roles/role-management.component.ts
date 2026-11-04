import { Component, OnInit, signal } from "@angular/core";
import { CommonModule } from "@angular/common";
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from "@angular/forms";
import { RoleService, Permission } from "../../../core/services/role.service";
import { CreateRolePayload, Role, RoleUser } from "../../../core/models/user.model";

@Component({
  selector: "app-role-management",
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <div class="role-management space-y-6">
      <!-- نوار عنوان و دکمههای عملیاتی -->
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
        <div>
          <h1 class="text-xl font-bold text-slate-800">ماتریس نقشها و سطوح دسترسی</h1>
          <p class="text-xs text-slate-500 mt-1">
            مدیریت نقشهای حاکمیت داده، تفکیک دسترسیهای سیستمی و بررسی کاربران منتسب به هر نقش.
          </p>
        </div>
        <button
          (click)="openCreateModal()"
          class="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors cursor-pointer"
        >
          <i class="pi pi-plus text-xs"></i>
          <span>تعریف نقش جدید</span>
        </button>
      </div>

      <!-- وضعیت بارگذاری -->
      <div *ngIf="loading()" class="p-8 text-center text-slate-500 text-xs bg-white rounded-xl border border-slate-200">
        <i class="pi pi-spin pi-spinner text-2xl text-blue-600 mb-2"></i>
        <div>در حال بارگذاری نقشها و مجوزهای دسترسی...</div>
      </div>

      <!-- شبکه کارتهای نقشها -->
      <div *ngIf="!loading()" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div
          *ngFor="let role of roles()"
          class="bg-white rounded-xl border border-slate-200 shadow-sm p-5 flex flex-col justify-between hover:border-blue-300 hover:shadow-md transition-all"
        >
          <div>
            <div class="flex items-start justify-between gap-2 mb-3">
              <div>
                <h3 class="font-bold text-slate-800 text-sm">{{ role.name }}</h3>
                <div class="font-mono text-[11px] text-blue-600 font-semibold dir-ltr text-end">{{ role.code }}</div>
              </div>
              <span
                class="px-2 py-0.5 rounded text-[10px] font-semibold"
                [ngClass]="role.is_system ? 'bg-purple-50 text-purple-700 border border-purple-200' : 'bg-emerald-50 text-emerald-700 border border-emerald-200'"
              >
                {{ role.is_system ? 'نقش سیستمی' : 'نقش سفارشی' }}
              </span>
            </div>

            <p class="text-xs text-slate-500 mb-4 leading-relaxed">{{ role.description || 'بدون توضیحات ثبت شده.' }}</p>

            <!-- بخش مجوزهای نقش -->
            <div class="mb-4">
              <div class="text-[11px] font-semibold text-slate-700 mb-2 flex items-center justify-between">
                <span>مجوزهای این نقش</span>
                <span class="text-slate-400 font-normal">({{ role.permissions.length }} مورد)</span>
              </div>
              <div class="flex flex-wrap gap-1.5 max-h-28 overflow-y-auto">
                <span
                  *ngFor="let perm of role.permissions"
                  class="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-50 text-slate-700 border border-slate-200"
                >
                  {{ perm }}
                </span>
                <span *ngIf="role.permissions.length === 0" class="text-slate-400 italic text-[11px]">
                  هیچ مجوزی مستقیماً به این نقش داده نشده است.
                </span>
              </div>
            </div>
          </div>

          <!-- نوار پایین کارت: تعداد کاربران و دکمه مشاهده کاربران -->
          <div class="pt-3 border-t border-slate-100 flex items-center justify-between">
            <div class="flex items-center gap-1.5 text-xs text-slate-600">
              <i class="pi pi-users text-slate-400 text-xs"></i>
              <span class="font-semibold text-slate-800">{{ role.assigned_user_count || 0 }}</span>
              <span>کاربر منتسب</span>
            </div>
            <button
              (click)="inspectRoleUsers(role)"
              class="px-2.5 py-1 text-xs text-blue-600 hover:text-blue-800 hover:bg-blue-50 font-medium rounded-lg transition-colors cursor-pointer"
            >
              مشاهده کاربران
            </button>
          </div>
        </div>
      </div>

      <!-- راهنمای ماژولها و مجوزهای سراسری سیستم -->
      <div *ngIf="!loading() && permissions().length > 0" class="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
        <div class="mb-4">
          <h2 class="text-sm font-bold text-slate-800">فهرست کل مجوزهای امنیتی سامانه</h2>
          <p class="text-xs text-slate-500 mt-0.5">مجوزهای ریزدانهای که توسط لایه سرور بررسی و اعمال میشوند.</p>
        </div>

        <div class="overflow-x-auto">
          <table class="w-full text-start text-xs">
            <thead class="bg-slate-50 text-slate-600 border-b border-slate-200 font-semibold">
              <tr>
                <th class="px-4 py-3 text-start">ماژول</th>
                <th class="px-4 py-3 text-start">کد مجوز</th>
                <th class="px-4 py-3 text-start">عنوان دسترسی</th>
                <th class="px-4 py-3 text-start">توضیحات</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr *ngFor="let p of permissions()" class="hover:bg-slate-50/70">
                <td class="px-4 py-3 font-semibold text-blue-600 uppercase text-[10px]">{{ p.module }}</td>
                <td class="px-4 py-3 font-mono font-medium text-slate-800 dir-ltr text-end">{{ p.code }}</td>
                <td class="px-4 py-3 text-slate-700">{{ p.name }}</td>
                <td class="px-4 py-3 text-slate-400">{{ p.description || '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- پنجره مودال: ایجاد نقش جدید -->
      <div *ngIf="isCreateModalOpen()" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
        <div class="bg-white rounded-xl shadow-xl border border-slate-200 w-full max-w-lg overflow-hidden animate-in fade-in zoom-in-95 duration-150">
          <div class="flex items-center justify-between px-6 py-4 border-b border-slate-200 bg-slate-50/50">
            <h2 class="text-sm font-bold text-slate-800 flex items-center gap-2">
              <i class="pi pi-shield text-blue-600"></i>
              <span>تعریف نقش سفارشی جدید</span>
            </h2>
            <button (click)="closeCreateModal()" class="text-slate-400 hover:text-slate-600 cursor-pointer">
              <i class="pi pi-times"></i>
            </button>
          </div>

          <form [formGroup]="roleForm" (ngSubmit)="submitNewRole()" class="p-6 space-y-4">
            <div *ngIf="createError()" class="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs">
              {{ createError() }}
            </div>

            <div>
              <label class="block text-xs font-semibold text-slate-700 mb-1">عنوان نقش (فارسی) *</label>
              <input
                type="text"
                formControlName="name"
                placeholder="مثال: تحلیلگر دادههای مالی"
                class="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label class="block text-xs font-semibold text-slate-700 mb-1">شناسه سیستمی نقش (لاتین بزرگ) *</label>
              <input
                type="text"
                formControlName="code"
                placeholder="مثال: ROLE_FINANCE_ANALYST"
                class="w-full px-3 py-2 text-xs font-mono border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dir-ltr text-end"
              />
            </div>

            <div>
              <label class="block text-xs font-semibold text-slate-700 mb-1">توضیحات و دامنه وظایف</label>
              <textarea
                formControlName="description"
                rows="2"
                placeholder="توضیح مختصری از محدوده اختیارات این نقش..."
                class="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              ></textarea>
            </div>

            <div>
              <label class="block text-xs font-semibold text-slate-700 mb-2">انتخاب مجوزهای دسترسی</label>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-40 overflow-y-auto p-3 border border-slate-200 rounded-lg bg-slate-50/50">
                <label *ngFor="let perm of permissions()" class="flex items-center gap-2 text-xs text-slate-700 cursor-pointer">
                  <input
                    type="checkbox"
                    [value]="perm.code"
                    (change)="togglePermission(perm.code, $event)"
                    class="rounded text-blue-600 focus:ring-blue-500"
                  />
                  <span>{{ perm.name }}</span>
                </label>
              </div>
            </div>

            <div class="flex items-center justify-end gap-3 pt-4 border-t border-slate-200">
              <button
                type="button"
                (click)="closeCreateModal()"
                class="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-800 cursor-pointer"
              >
                انصراف
              </button>
              <button
                type="submit"
                [disabled]="roleForm.invalid || creating()"
                class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors disabled:opacity-50 cursor-pointer"
              >
                <span *ngIf="!creating()">ثبت و ذخیره نقش</span>
                <span *ngIf="creating()">در حال ذخیره...</span>
              </button>
            </div>
          </form>
        </div>
      </div>

      <!-- پنجره مودال: کاربران منتسب به نقش -->
      <div *ngIf="isUserModalOpen()" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
        <div class="bg-white rounded-xl shadow-xl border border-slate-200 w-full max-w-lg overflow-hidden animate-in fade-in zoom-in-95 duration-150">
          <div class="flex items-center justify-between px-6 py-4 border-b border-slate-200 bg-slate-50/50">
            <div>
              <h2 class="text-sm font-bold text-slate-800 flex items-center gap-2">
                <i class="pi pi-users text-blue-600"></i>
                <span>کاربران دارای نقش: {{ activeRoleForUsers()?.name }}</span>
              </h2>
              <div class="text-[11px] font-mono text-slate-400 mt-0.5 dir-ltr text-end">{{ activeRoleForUsers()?.code }}</div>
            </div>
            <button (click)="closeUserModal()" class="text-slate-400 hover:text-slate-600 cursor-pointer">
              <i class="pi pi-times"></i>
            </button>
          </div>

          <div class="p-6">
            <div *ngIf="loadingUsers()" class="p-8 text-center text-slate-500 text-xs">
              <i class="pi pi-spin pi-spinner text-xl text-blue-600 mb-2"></i>
              <div>در حال بارگذاری لیست کاربران...</div>
            </div>

            <div *ngIf="!loadingUsers() && roleUsers().length === 0" class="p-8 text-center text-slate-400">
              <i class="pi pi-user-minus text-3xl mb-2 text-slate-300"></i>
              <div class="text-xs font-semibold text-slate-600">هیچ کاربری به این نقش تخصیص نیافته است.</div>
              <div class="text-[11px] text-slate-400 mt-1">میتوانید از منوی «مدیریت کاربران» این نقش را به حسابها تخصیص دهید.</div>
            </div>

            <div *ngIf="!loadingUsers() && roleUsers().length > 0" class="max-h-72 overflow-y-auto space-y-2">
              <div
                *ngFor="let u of roleUsers()"
                class="flex items-center justify-between p-3 rounded-lg border border-slate-100 bg-slate-50/50"
              >
                <div class="flex items-center gap-3">
                  <div class="w-8 h-8 rounded-full bg-blue-100 text-blue-700 font-bold flex items-center justify-center uppercase text-xs">
                    {{ u.username.charAt(0) }}
                  </div>
                  <div>
                    <div class="text-xs font-semibold text-slate-800">{{ u.full_name || u.username }}</div>
                    <div class="text-[11px] text-slate-500 font-mono">{{ u.email }}</div>
                  </div>
                </div>
                <span
                  class="px-2 py-0.5 rounded text-[10px] font-medium"
                  [ngClass]="u.is_active ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-slate-100 text-slate-500'"
                >
                  {{ u.is_active ? 'فعال' : 'غیرفعال' }}
                </span>
              </div>
            </div>

            <div class="flex justify-end pt-4 mt-4 border-t border-slate-100">
              <button
                type="button"
                (click)="closeUserModal()"
                class="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg transition-colors cursor-pointer"
              >
                بستن
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
})
export class RoleManagementComponent implements OnInit {
  roles = signal<Role[]>([]);
  permissions = signal<Permission[]>([]);
  loading = signal(true);

  // ایجاد نقش
  isCreateModalOpen = signal(false);
  creating = signal(false);
  createError = signal<string | null>(null);
  selectedPermissions: string[] = [];
  roleForm: FormGroup;

  // مشاهده کاربران نقش
  isUserModalOpen = signal(false);
  activeRoleForUsers = signal<Role | null>(null);
  roleUsers = signal<RoleUser[]>([]);
  loadingUsers = signal(false);

  constructor(
    private roleService: RoleService,
    private fb: FormBuilder
  ) {
    this.roleForm = this.fb.group({
      code: ["", [Validators.required, Validators.pattern(/^[A-Z0-9_]+$/)]],
      name: ["", [Validators.required, Validators.minLength(2)]],
      description: [""],
    });
  }

  ngOnInit(): void {
    this.loadData();
  }

  loadData(): void {
    this.loading.set(true);
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

  openCreateModal(): void {
    this.roleForm.reset();
    this.selectedPermissions = [];
    this.createError.set(null);
    this.isCreateModalOpen.set(true);
  }

  closeCreateModal(): void {
    this.isCreateModalOpen.set(false);
  }

  togglePermission(code: string, event: Event): void {
    const checked = (event.target as HTMLInputElement).checked;
    if (checked) {
      if (!this.selectedPermissions.includes(code)) {
        this.selectedPermissions.push(code);
      }
    } else {
      this.selectedPermissions = this.selectedPermissions.filter((c) => c !== code);
    }
  }

  submitNewRole(): void {
    if (this.roleForm.invalid) return;

    this.creating.set(true);
    this.createError.set(null);

    const payload: CreateRolePayload = {
      ...this.roleForm.value,
      permission_codes: this.selectedPermissions,
    };

    this.roleService.createRole(payload).subscribe({
      next: (newRole) => {
        this.roles.update((prev) => [...prev, newRole]);
        this.creating.set(false);
        this.closeCreateModal();
      },
      error: (err: { error?: { detail?: string } }) => {
        this.creating.set(false);
        this.createError.set(err.error?.detail || "خطا در ایجاد نقش جدید.");
      },
    });
  }

  inspectRoleUsers(role: Role): void {
    this.activeRoleForUsers.set(role);
    this.roleUsers.set([]);
    this.loadingUsers.set(true);
    this.isUserModalOpen.set(true);

    this.roleService.getRoleUsers(role.id).subscribe({
      next: (users) => {
        this.roleUsers.set(users);
        this.loadingUsers.set(false);
      },
      error: () => this.loadingUsers.set(false),
    });
  }

  closeUserModal(): void {
    this.isUserModalOpen.set(false);
    this.activeRoleForUsers.set(null);
  }
}
