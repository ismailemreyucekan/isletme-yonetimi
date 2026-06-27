import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { authApi } from "@shared/api/auth";
import { ordersApi, tablesApi } from "@shared/api/pos";
import type { TableWithStatus } from "@shared/types";
import { Button } from "@shared/ui/Button";
import { Card } from "@shared/ui/Card";

function money(v: number | string) {
  return `₺${Number(v).toFixed(2)}`;
}

export function TablesPage() {
  const qc = useQueryClient();
  const navigate = useNavigate();
  const [manage, setManage] = useState(false);

  const { data: tables = [], isLoading } = useQuery({
    queryKey: ["tables"],
    queryFn: tablesApi.list,
    refetchInterval: 5000,
  });

  const { data: restaurant } = useQuery({
    queryKey: ["my-restaurant"],
    queryFn: authApi.myRestaurant,
  });

  // Müşteri uygulaması ayrı origin'de (5174). Geliştirme için 5173'ten 5174'e çevir.
  const customerOrigin =
    import.meta.env.VITE_CUSTOMER_ORIGIN ??
    window.location.origin.replace(":5173", ":5174");

  const customerUrl = (t: TableWithStatus) =>
    `${customerOrigin}/r/${restaurant?.slug}/t/${t.qr_token}`;

  const bulkCreate = useMutation({
    mutationFn: (count: number) => tablesApi.bulkCreate(count),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tables"] }),
  });

  const addOne = useMutation({
    mutationFn: () => tablesApi.create(`Masa ${tables.length + 1}`, tables.length + 1),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tables"] }),
  });

  const removeTable = useMutation({
    mutationFn: (id: string) => tablesApi.remove(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tables"] }),
  });

  const openOrder = useMutation({
    mutationFn: (table: TableWithStatus) =>
      table.active_order_id
        ? Promise.resolve({ id: table.active_order_id })
        : ordersApi.open(table.id),
    onSuccess: (order, table) => {
      navigate(`/staff/pos/${table.id}/${order.id}`);
    },
  });

  if (isLoading) return <div className="p-8 text-slate-500">Yükleniyor…</div>;

  return (
    <div className="p-4">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-800">Masa Planı</h2>
          <p className="text-sm text-slate-500">
            Boş masaya dokun → sipariş aç · Dolu masaya dokun → hesabı aç
          </p>
        </div>
        <Button
          variant="secondary"
          onClick={() => setManage((m) => !m)}
        >
          {manage ? "Bitti" : "Masaları Yönet"}
        </Button>
      </div>

      {manage && (
        <Card className="mb-4 flex flex-wrap items-center gap-3 p-4">
          <span className="text-sm text-slate-600">Hızlı kurulum:</span>
          <Button onClick={() => addOne.mutate()} loading={addOne.isPending}>
            + 1 Masa
          </Button>
          {[5, 10, 20].map((n) => (
            <Button
              key={n}
              variant="secondary"
              onClick={() => bulkCreate.mutate(n)}
              loading={bulkCreate.isPending}
            >
              + {n} Masa
            </Button>
          ))}
          <span className="text-xs text-slate-400">
            🔗 müşteri QR bağlantısını açar/kopyalar · × boş masayı siler.
          </span>
        </Card>
      )}

      {tables.length === 0 ? (
        <div className="flex flex-col items-center gap-3 py-16 text-slate-400">
          <p>Henüz masa yok.</p>
          <Button onClick={() => bulkCreate.mutate(10)} loading={bulkCreate.isPending}>
            10 Masa Oluştur
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
          {tables.map((t) => {
            const occupied = t.status === "occupied";
            const remaining = t.active_total - t.active_paid_total;
            return (
              <button
                key={t.id}
                onClick={() => openOrder.mutate(t)}
                className={[
                  "relative flex aspect-square flex-col items-center justify-center rounded-xl border-2 p-2 transition-all",
                  occupied
                    ? "border-amber-400 bg-amber-50 hover:bg-amber-100"
                    : "border-emerald-300 bg-emerald-50 hover:bg-emerald-100",
                ].join(" ")}
              >
                {manage && !occupied && (
                  <span
                    role="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      if (confirm(`${t.name} silinsin mi?`)) removeTable.mutate(t.id);
                    }}
                    className="absolute right-1 top-1 flex h-6 w-6 items-center justify-center rounded-full bg-red-500 text-xs text-white hover:bg-red-600"
                  >
                    ×
                  </span>
                )}
                {manage && (
                  <span
                    role="button"
                    title="Müşteri QR bağlantısı"
                    onClick={(e) => {
                      e.stopPropagation();
                      const url = customerUrl(t);
                      navigator.clipboard?.writeText(url);
                      window.open(url, "_blank");
                    }}
                    className="absolute left-1 top-1 flex h-6 w-6 items-center justify-center rounded-full bg-slate-700 text-xs text-white hover:bg-slate-900"
                  >
                    🔗
                  </span>
                )}
                <span className="text-base font-semibold text-slate-800">{t.name}</span>
                <span
                  className={[
                    "mt-1 text-xs font-medium",
                    occupied ? "text-amber-700" : "text-emerald-600",
                  ].join(" ")}
                >
                  {occupied ? "Dolu" : "Boş"}
                </span>
                {occupied && (
                  <span className="mt-1 text-sm font-bold text-slate-900">
                    {money(remaining)}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
