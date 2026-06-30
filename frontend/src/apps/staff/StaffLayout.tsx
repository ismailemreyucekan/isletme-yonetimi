import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";

import { authApi } from "@shared/api/auth";
import { connectKdsSocket } from "@shared/api/kds";
import { waiterCallsApi } from "@shared/api/pos";
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

      {/* Garson çağrısı: hangi personel sayfasında olursak olalım anında düşer */}
      <WaiterCallNotifier />
    </div>
  );
}

// Canlı garson çağrısı bildirimi — "pos" kanalını dinler, ekranın sağ üstüne
// açılır kart(lar) düşürür. Kartdan "Geldim" ile çağrı kapatılır.
function WaiterCallNotifier() {
  const qc = useQueryClient();
  const [alerts, setAlerts] = useState<{ id: string; table: string }[]>([]);

  const resolve = useMutation({
    mutationFn: (id: string) => waiterCallsApi.resolve(id),
    onSuccess: (_data, id) => {
      setAlerts((a) => a.filter((x) => x.id !== id));
      qc.invalidateQueries({ queryKey: ["waiter-calls"] });
    },
  });

  useEffect(() => {
    const disconnect = connectKdsSocket((event) => {
      if (event.type !== "waiter.called") return;
      const id = event.call_id ?? `${Date.now()}`;
      setAlerts((a) =>
        [{ id, table: event.table_name ?? "Masa" }, ...a.filter((x) => x.id !== id)].slice(0, 10),
      );
      // Açık olan listeler (Dashboard bölümü) de anında tazelensin.
      qc.invalidateQueries({ queryKey: ["waiter-calls"] });
    }, "pos");
    return disconnect;
  }, [qc]);

  const dismiss = (id: string) => setAlerts((a) => a.filter((x) => x.id !== id));

  if (alerts.length === 0) return null;

  return (
    <div className="fixed right-4 top-20 z-[100] flex w-80 max-w-[calc(100vw-2rem)] flex-col gap-2">
      {alerts.map((a) => (
        <div
          key={a.id}
          className="flex items-center justify-between gap-3 rounded-xl border border-amber-300 bg-amber-50 px-4 py-3 shadow-xl"
        >
          <div className="flex min-w-0 items-center gap-2">
            <span className="text-2xl">🔔</span>
            <div className="min-w-0">
              <p className="truncate font-bold text-amber-900">{a.table}</p>
              <p className="text-xs text-amber-700">garson çağırıyor</p>
            </div>
          </div>
          <div className="flex shrink-0 items-center gap-1">
            <button
              type="button"
              disabled={resolve.isPending}
              onClick={() => resolve.mutate(a.id)}
              className="rounded-lg bg-amber-600 px-3 py-1.5 text-sm font-semibold text-white transition-colors hover:bg-amber-700 disabled:opacity-60"
            >
              Geldim
            </button>
            <button
              type="button"
              onClick={() => dismiss(a.id)}
              aria-label="Kapat"
              className="flex h-8 w-8 items-center justify-center rounded-lg text-lg text-amber-700 hover:bg-amber-100"
            >
              ✕
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
