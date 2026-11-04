import { Component, OnInit, computed, signal } from "@angular/core";
import { CommonModule } from "@angular/common";
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from "@angular/forms";
import { UserService } from "../../../core/services/user.service";
import { RoleService } from "../../../core/services/role.service";
import { Role, User } from "../../../core/models/user.model";

@Component({
  selector: "app-user-management",
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <div class="user-management space-y-6">
      <!-- نوار عنوان و دکمههای عملیاتی -->
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
        <div>
          <h1 class="text-xl font-bold text-slate-800">مدیریت کاربران کاتالوگ</h1>
          <p class="text-xs text-slate-500 mt-1">مدیریت حسابهای کاربری، تخصیص نقشهای حاکمیتی و رصد وضعیت دسترسیها.</p>
        </div>
        <button
          (click)="openModal()"
          class="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors cursor-pointer"
        >
          <i class="pi pi-user-plus text-sm"></i>
          <span>تعریف کاربر جدید</span>
        </button>
      </div>

      <!-- کارتهای آماری وضعیت -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <div class="text-xs font-medium text-slate-500">کل کاربران</div>
            <div class="text-2xl font-bold text-slate-800 mt-1">{{ users().length }}</div>
          </div>
          <div class="w-10 h-10 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
            <i class="pi pi-users text-lg"></i>
          </div>
        </div>
        <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <div class="text-xs font-medium text-slate-500">حسابهای فعال</div>
            <div class="text-2xl font-bold text-emerald-600 mt-1">{{ activeUserCount() }}</div>
          </div>
          <div class="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
            <i class="pi pi-check-circle text-lg"></i>
          </div>
        </div>
        <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <div class="text-xs font-medium text-slate-500">مدیران ارشد سیستم</div>
            <div class="text-2xl font-bold text-purple-600 mt-1">{{ superuserCount() }}</div>
          </div>
          <div class="w-10 h-10 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center">
            <i class="pi pi-shield text-lg"></i>
          </div>
        </div>
      </div>

      <!-- جستجو و فیلترها -->
      <div class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
        <div class="relative">
          <i class="pi pi-search absolute start-3 top-1/2 -translate-y-1/2 text-slate-400 text-sm"></i>
          <input
            type="text"
            [value]="searchQuery()"
            (input)="onSearchInput($event)"
            placeholder="جستجو بر اساس نام کاربری، نام کامل یا ایمیل..."
            class="w-full ps-10 pe-4 py-2 text-xs border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      <!-- جدول نمایش کاربران -->
      <div class="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div *ngIf="loading()" class="p-8 text-center text-slate-500 text-xs">
          <i class="pi pi-spin pi-spinner text-2xl text-blue-600 mb-2"></i>
          <div>در حال بارگذاری کاربران کاتالوگ...</div>
        </div>

        <div *ngIf="errorMessage()" class="p-4 bg-rose-50 border-b border-rose-200 text-rose-700 text-xs">
          {{ errorMessage() }}
        </div>

        <div *ngIf="!loading() && filteredUsers().length === 0" class="p-12 text-center text-slate-400">
          <i class="pi pi-users text-4xl mb-2 text-slate-300"></i>
          <div class="text-sm font-semibold text-slate-600">کاربری یافت نشد</div>
          <div class="text-xs text-slate-400 mt-1">میتوانید عبارت جستجو را تغییر دهید یا کاربر جدیدی تعریف نمایید.</div>
        </div>

        <div *ngIf="!loading() && filteredUsers().length > 0" class="overflow-x-auto">
          <table class="w-full text-start text-xs">
            <thead class="bg-slate-50 text-slate-600 border-b border-slate-200 font-semibold">
              <tr>
                <th class="px-6 py-3.5 text-start">مشخصات کاربر</th>
                <th class="px-6 py-3.5 text-start">ایمیل سازمانی</th>
                <th class="px-6 py-3.5 text-start">نقشهای منتسب</th>
                <th class="px-6 py-3.5 text-start">وضعیت حساب</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr *ngFor="let u of filteredUsers()" class="hover:bg-slate-50/70 transition-colors">
                <td class="px-6 py-4">
                  <div class="flex items-center gap-3">
                    <div class="w-8 h-8 rounded-full bg-blue-100 text-blue-700 font-bold flex items-center justify-center uppercase text-xs">
                      {{ u.username.charAt(0) }}
                    </div>
                    <div>
                      <div class="font-semibold text-slate-800 flex items-center gap-1.5">
                        <span>{{ u.username }}</span>
                        <span *ngIf="u.is_superuser" class="px-1.5 py-0.5 rounded text-[10px] font-medium bg-purple-100 text-purple-700">مدیر ارشد</span>
                      </div>
                      <div class="text-[11px] text-slate-400">{{ u.full_name || 'بدون نام ثبتشده' }}</div>
                    </div>
                  </div>
                </td>
                <td class="px-6 py-4 text-slate-600 font-mono text-[11px] dir-ltr text-end">{{ u.email }}</td>
                <td class="px-6 py-4">
                  <div class="flex flex-wrap gap-1">
                    <span
                      *ngFor="let r of u.roles"
                      class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-blue-50 text-blue-700 border border-blue-200"
                    >
                      {{ r }}
                    </span>
                    <span *ngIf="u.roles.length === 0" class="text-slate-400 italic text-[11px]">بدون نقش</span>
                  </div>
                </td>
                <td class="px-6 py-4">
                  <span
                    class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium"
                    [ngClass]="u.is_active ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-slate-100 text-slate-500 border border-slate-200'"
                  >
                    <span class="w-1.5 h-1.5 rounded-full" [ngClass]="u.is_active ? 'bg-emerald-500' : 'bg-slate-400'"></span>
                    <span>{{ u.is_active ? 'فعال' : 'غیرفعال' }}</span>
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- پنجره مودال: ثبت کاربر جدید -->
      <div *ngIf="isModalOpen()" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
        <div class="bg-white rounded-xl shadow-xl border border-slate-200 w-full max-w-lg overflow-hidden animate-in fade-in zoom-in-95 duration-150">
          <div class="flex items-center justify-between px-6 py-4 border-b border-slate-200 bg-slate-50/50">
            <h2 class="text-sm font-bold text-slate-800 flex items-center gap-2">
              <i class="pi pi-user-plus text-blue-600"></i>
              <span>تعریف کاربر جدید</span>
            </h2>
            <button (click)="closeModal()" class="text-slate-400 hover:text-slate-600 cursor-pointer">
              <i class="pi pi-times"></i>
            </button>
          </div>

          <form [formGroup]="userForm" (ngSubmit)="submitUser()" class="p-6 space-y-4">
            <div *ngIf="createError()" class="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs">
              {{ createError() }}
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label class="block text-xs font-semibold text-slate-700 mb-1">نام کاربری (لاتین) *</label>
                <input
                  type="text"
                  formControlName="username"
                  placeholder="مثال: jdoe"
                  class="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dir-ltr text-end"
                />
              </div>
              <div>
                <label class="block text-xs font-semibold text-slate-700 mb-1">نام و نام خانوادگی</label>
                <input
                  type="text"
                  formControlName="full_name"
                  placeholder="مثال: علی احمدی"
                  class="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <div>
              <label class="block text-xs font-semibold text-slate-700 mb-1">ایمیل سازمانی *</label>
              <input
                type="email"
                formControlName="email"
                placeholder="user@example.com"
                class="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dir-ltr text-end"
              />
            </div>

            <div>
              <label class="block text-xs font-semibold text-slate-700 mb-1">کلمه عبور اولیه *</label>
              <input
                type="password"
                formControlName="password"
                placeholder="حداقل ۸ نویسه"
                class="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dir-ltr text-end"
              />
            </div>

            <div>
              <label class="block text-xs font-semibold text-slate-700 mb-2">تخصیص نقشهای کاربری</label>
              <div class="grid grid-cols-2 gap-2 max-h-36 overflow-y-auto p-2 border border-slate-200 rounded-lg bg-slate-50/50">
                <label *ngFor="let role of availableRoles()" class="flex items-center gap-2 text-xs text-slate-700 cursor-pointer">
                  <input
                    type="checkbox"
                    [value]="role.code"
                    (change)="toggleRole(role.code, $event)"
                    class="rounded text-blue-600 focus:ring-blue-500"
                  />
                  <span>{{ role.name }}</span>
                </label>
              </div>
            </div>

            <div class="flex items-center justify-end gap-3 pt-4 border-t border-slate-200">
              <button
                type="button"
                (click)="closeModal()"
                class="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-800 cursor-pointer"
              >
                انصراف
              </button>
              <button
                type="submit"
                [disabled]="userForm.invalid || creating()"
                class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow-sm transition-colors disabled:opacity-50 cursor-pointer"
              >
                <span *ngIf="!creating()">ایجاد و ثبت حساب</span>
                <span *ngIf="creating()">در حال ایجاد...</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  `,
})
export class UserManagementComponent implements OnInit {
  users = signal<User[]>([]);
  availableRoles = signal<Role[]>([]);
  loading = signal(true);
  creating = signal(false);
  errorMessage = signal<string | null>(null);
  createError = signal<string | null>(null);
  searchQuery = signal("");
  isModalOpen = signal(false);

  selectedRoleCodes: string[] = [];

  userForm: FormGroup;

  constructor(
    private userService: UserService,
    private roleService: RoleService,
    private fb: FormBuilder
  ) {
    this.userForm = this.fb.group({
      username: ["", [Validators.required, Validators.minLength(2)]],
      email: ["", [Validators.required, Validators.email]],
      password: ["", [Validators.required, Validators.minLength(8)]],
      full_name: [""],
    });
  }

  filteredUsers = computed(() => {
    const q = this.searchQuery().toLowerCase().trim();
    if (!q) return this.users();
    return this.users().filter(
      (u) =>
        u.username.toLowerCase().includes(q) ||
        (u.full_name && u.full_name.toLowerCase().includes(q)) ||
        u.email.toLowerCase().includes(q)
    );
  });

  activeUserCount = computed(() => this.users().filter((u) => u.is_active).length);
  superuserCount = computed(() => this.users().filter((u) => u.is_superuser).length);

  ngOnInit(): void {
    this.loadData();
  }

  loadData(): void {
    this.loading.set(true);
    this.errorMessage.set(null);

    this.userService.getUsers().subscribe({
      next: (data) => {
        this.users.set(data);
        this.loading.set(false);
      },
      error: (err: { error?: { detail?: string } }) => {
        this.errorMessage.set(err.error?.detail || "خطا در بارگذاری اطلاعات کاربران از سرور.");
        this.loading.set(false);
      },
    });

    this.roleService.getRoles().subscribe({
      next: (roles) => this.availableRoles.set(roles),
      error: () => {},
    });
  }

  onSearchInput(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.searchQuery.set(input.value);
  }

  openModal(): void {
    this.userForm.reset();
    this.selectedRoleCodes = [];
    this.createError.set(null);
    this.isModalOpen.set(true);
  }

  closeModal(): void {
    this.isModalOpen.set(false);
  }

  toggleRole(roleCode: string, event: Event): void {
    const checked = (event.target as HTMLInputElement).checked;
    if (checked) {
      if (!this.selectedRoleCodes.includes(roleCode)) {
        this.selectedRoleCodes.push(roleCode);
      }
    } else {
      this.selectedRoleCodes = this.selectedRoleCodes.filter((c) => c !== roleCode);
    }
  }

  submitUser(): void {
    if (this.userForm.invalid) return;

    this.creating.set(true);
    this.createError.set(null);

    const payload = {
      ...this.userForm.value,
      role_codes: this.selectedRoleCodes,
    };

    this.userService.createUser(payload).subscribe({
      next: (newUser) => {
        this.users.update((prev) => [newUser, ...prev]);
        this.creating.set(false);
        this.closeModal();
      },
      error: (err: { error?: { detail?: string } }) => {
        this.creating.set(false);
        this.createError.set(err.error?.detail || "خطا در ایجاد حساب کاربری.");
      },
    });
  }
}
