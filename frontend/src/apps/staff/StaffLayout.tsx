import { useQuery } from "@tanstack/react-query";
import { NavLink, Outlet, useNavigate } from "react-router-dom";

import { authApi } from "@shared/api/auth";
import { useAuthStore } from "@shared/store/authStore";

const NAV = [
  { to: "/staff", label: "Ana Sayfa", end: true },
  { to: "/staff/tables", label: "Masalar (POS)", end: false },
  { to: "/staff/menu", label: "Menü Yönetimi", end: false },
  { to: "/staff/coupons", label: "Kuponlar", end: false },
  { to: "/kds", label: "Mutfak (KDS)", end: false },
];

export function StaffLayout() {
  const navigate = useNavigate();
  const logout = useAuthStore((s) => s.logout);
  const restaurantQuery = useQuery({ queryKey: ["my-restaurant"], queryFn: authApi.myRestaurant });

  const handleLogout = () => {
    logout();
    navigate("/staff/login", { replace: true });
  };

  return (
    <div className="flex min-h-screen flex-col bg-slate-100">
      <header className="flex items-center justify-between border-b bg-white px-6 py-3 shadow-sm">
        <div className="flex items-center gap-6">
          <span className="text-lg font-bold text-brand-800">Kasa</span>
          <nav className="flex gap-1">
            {NAV.map(({ to, label, end }) => (
              <NavLink
                key={to}
                to={to}
                end={end}
                className={({ isActive }) =>
                  [
                    "rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
                    isActive
                      ? "bg-brand-600 text-white"
                      : "text-slate-600 hover:bg-slate-100",
                  ].join(" ")
                }
              >
                {label}
              </NavLink>
            ))}
          </nav>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm text-slate-500">{restaurantQuery.data?.name}</span>
          <button
            onClick={handleLogout}
            className="rounded-md border border-slate-200 px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-50 transition-colors"
          >
            Çıkış
          </button>
        </div>
      </header>
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
