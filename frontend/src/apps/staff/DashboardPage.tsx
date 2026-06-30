import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { authApi } from "@shared/api/auth";
import { dashboardApi, waiterCallsApi } from "@shared/api/pos";
import type { ActiveOrderSummary, WaiterCall } from "@shared/types";
import { Card } from "@shared/ui/Card";

const money = (v: number) => `₺${Number(v).toFixed(2)}`;

const SOURCE_LABELS: Record<string, string> = {
  dine_in: "Masa",
  takeaway: "Paket",
  qr_self_order: "QR Sipariş",
};

export function DashboardPage() {
  const navigate = useNavigate();
  const qc = useQueryClient();

  const restaurantQuery = useQuery({
    queryKey: ["my-restaurant"],
    queryFn: authApi.myRestaurant,
  });

  const summaryQuery = useQuery({
    queryKey: ["dashboard-summary"],
    queryFn: dashboardApi.summary,
    refetchInterval: 15_000, // canlı tut: 15 sn'de bir yenile
    refetchOnWindowFocus: true,
  });

  const waiterCallsQuery = useQuery({
    queryKey: ["waiter-calls"],
    queryFn: waiterCallsApi.list,
    refetchInterval: 10_000,
    refetchOnWindowFocus: true,
  });

  const resolveCall = useMutation({
    mutationFn: (id: string) => waiterCallsApi.resolve(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["waiter-calls"] }),
  });

  const s = summaryQuery.data;
  const calls = waiterCallsQuery.data ?? [];

  return (
    <div className="mx-auto max-w-5xl p-6">
      <header className="mb-6 flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">
            {restaurantQuery.data?.name ?? "Yükleniyor…"}
          </h1>
          <p className="text-sm text-slate-500">İşletme Özeti</p>
        </div>
        {summaryQuery.isFetching && (
          <span className="text-xs text-slate-400">Güncelleniyor…</span>
        )}
      </header>

      {summaryQuery.isError && (
        <Card className="mb-4 border-red-200 bg-red-50 p-4 text-sm text-red-700">
          Özet bilgileri alınamadı. Sayfayı yenileyin.
        </Card>
      )}

      {/* Garson çağrıları (varsa öne çıkar) */}
      {calls.length > 0 && (
        <Card className="mb-4 border-amber-300 bg-amber-50 p-4">
          <div className="mb-3 flex items-center gap-2">
            <span className="text-lg">🔔</span>
            <h2 className="text-sm font-bold text-amber-800">
              Garson Çağrısı ({calls.length})
            </h2>
          </div>
          <ul className="flex flex-col gap-2">
            {calls.map((c) => (
              <WaiterCallRow
                key={c.id}
                call={c}
                busy={resolveCall.isPending}
                onResolve={() => resolveCall.mutate(c.id)}
              />
            ))}
          </ul>
        </Card>
      )}

      {/* Özet kartları */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Stat
          label="Dolu Masa"
          value={s ? `${s.occupied_tables} / ${s.total_tables}` : "—"}
          hint={s ? `${s.empty_tables} boş` : ""}
          accent="brand"
        />
        <Stat
          label="Aktif Sipariş"
          value={s ? String(s.active_orders) : "—"}
          hint="açık hesap"
          accent="amber"
        />
        <Stat
          label="Açık Hesap (Kalan)"
          value={s ? money(s.open_remaining) : "—"}
          hint={s ? `toplam ${money(s.open_total)}` : ""}
          accent="slate"
        />
        <Stat
          label="Bugünkü Ciro"
          value={s ? money(s.today_revenue) : "—"}
          hint={s ? `${s.today_payments} ödeme · bahşiş ${money(s.today_tips)}` : ""}
          accent="green"
        />
      </div>

      {/* Aktif siparişler */}
      <Card className="mt-6 p-0">
        <div className="flex items-center justify-between border-b border-slate-100 px-5 py-3">
          <h2 className="text-sm font-semibold text-slate-700">Aktif Siparişler</h2>
          <button
            type="button"
            onClick={() => navigate("/staff/tables")}
            className="text-xs font-medium text-brand-700 hover:underline"
          >
            Masa planı →
          </button>
        </div>

        {summaryQuery.isLoading ? (
          <p className="px-5 py-6 text-sm text-slate-500">Yükleniyor…</p>
        ) : !s || s.active_order_list.length === 0 ? (
          <p className="px-5 py-8 text-center text-sm text-slate-400">
            Şu an açık hesap yok.
          </p>
        ) : (
          <ul className="divide-y divide-slate-100">
            {s.active_order_list.map((o) => (
              <ActiveOrderRow key={o.order_id} order={o} onOpen={navigate} />
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}

function WaiterCallRow({
  call,
  busy,
  onResolve,
}: {
  call: WaiterCall;
  busy: boolean;
  onResolve: () => void;
}) {
  const mins = Math.floor((Date.now() - new Date(call.created_at).getTime()) / 60000);
  return (
    <li className="flex items-center justify-between gap-3 rounded-lg bg-white px-3 py-2.5 shadow-sm">
      <div className="min-w-0">
        <p className="font-semibold text-slate-800">{call.table_name ?? "Masa"}</p>
        <p className="text-xs text-slate-500">
          {mins <= 0 ? "az önce" : `${mins} dk önce`}
          {call.note ? ` · ${call.note}` : ""}
        </p>
      </div>
      <button
        type="button"
        disabled={busy}
        onClick={onResolve}
        className="shrink-0 rounded-lg bg-amber-600 px-3 py-2 text-sm font-semibold text-white transition-colors hover:bg-amber-700 disabled:opacity-60"
      >
        Geldim
      </button>
    </li>
  );
}

function Stat({
  label,
  value,
  hint,
  accent,
}: {
  label: string;
  value: string;
  hint?: string;
  accent: "brand" | "amber" | "green" | "slate";
}) {
  const ACCENTS: Record<string, string> = {
    brand: "text-brand-700",
    amber: "text-amber-600",
    green: "text-green-600",
    slate: "text-slate-800",
  };
  return (
    <Card className="p-4">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-400">
        {label}
      </p>
      <p className={`mt-1 text-2xl font-bold ${ACCENTS[accent]}`}>{value}</p>
      {hint && <p className="mt-0.5 text-xs text-slate-400">{hint}</p>}
    </Card>
  );
}

function ActiveOrderRow({
  order,
  onOpen,
}: {
  order: ActiveOrderSummary;
  onOpen: (path: string) => void;
}) {
  const clickable = Boolean(order.table_id);
  const open = () => {
    if (order.table_id) onOpen(`/staff/pos/${order.table_id}/${order.order_id}`);
  };
  return (
    <li
      onClick={open}
      className={[
        "flex items-center justify-between gap-3 px-5 py-3",
        clickable ? "cursor-pointer hover:bg-slate-50" : "",
      ].join(" ")}
    >
      <div className="min-w-0">
        <p className="font-medium text-slate-800">
          {order.table_name ?? SOURCE_LABELS[order.source] ?? "Sipariş"}
        </p>
        <p className="text-xs text-slate-400">
          {SOURCE_LABELS[order.source] ?? order.source} ·{" "}
          {new Date(order.opened_at).toLocaleTimeString("tr-TR", {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </p>
      </div>
      <div className="text-right">
        <p className="font-semibold text-slate-800">{money(order.total)}</p>
        {order.remaining > 0 ? (
          <p className="text-xs text-amber-600">kalan {money(order.remaining)}</p>
        ) : (
          <p className="text-xs text-green-600">ödendi</p>
        )}
      </div>
    </li>
  );
}
