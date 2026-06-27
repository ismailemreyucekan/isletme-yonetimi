import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { connectKdsSocket, kdsApi } from "@shared/api/kds";
import { useAuthStore } from "@shared/store/authStore";
import type { KdsItem, KdsTicket, KitchenStatus } from "@shared/types";

const SOURCE_LABEL: Record<string, string> = {
  dine_in: "Masa",
  takeaway: "Paket",
  qr_self_order: "QR",
};

// Mutfak panosundaki kalem (fiş bilgisiyle birlikte).
interface BoardItem extends KdsItem {
  table_name: string | null;
  source: string;
  opened_at: string;
}

const NEXT: Record<KitchenStatus, KitchenStatus> = {
  new: "preparing",
  preparing: "ready",
  ready: "served",
  served: "served",
};

function elapsedMin(iso: string): number {
  return Math.floor((Date.now() - new Date(iso).getTime()) / 60000);
}

export function KdsPage() {
  const qc = useQueryClient();
  const navigate = useNavigate();
  const logout = useAuthStore((s) => s.logout);
  const [, setTick] = useState(0);

  const { data: tickets = [], isLoading } = useQuery({
    queryKey: ["kds-tickets"],
    queryFn: kdsApi.tickets,
    refetchInterval: 5000,
  });

  // Canlı güncelleme: WebSocket olayında listeyi tazele.
  useEffect(() => {
    const disconnect = connectKdsSocket(() => {
      qc.invalidateQueries({ queryKey: ["kds-tickets"] });
    });
    return disconnect;
  }, [qc]);

  // Süre sayaçları için periyodik render.
  useEffect(() => {
    const t = setInterval(() => setTick((n) => n + 1), 30000);
    return () => clearInterval(t);
  }, []);

  const advance = useMutation({
    mutationFn: ({ id, next }: { id: string; next: KitchenStatus }) =>
      kdsApi.setItemStatus(id, next),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["kds-tickets"] }),
  });

  const board: BoardItem[] = tickets.flatMap((t: KdsTicket) =>
    t.items.map((it) => ({
      ...it,
      table_name: t.table_name,
      source: t.source,
      opened_at: t.opened_at,
    })),
  );

  const cols: { key: KitchenStatus; title: string; accent: string }[] = [
    { key: "new", title: "Yeni", accent: "border-amber-500" },
    { key: "preparing", title: "Hazırlanıyor", accent: "border-sky-500" },
    { key: "ready", title: "Hazır", accent: "border-emerald-500" },
  ];

  return (
    <div className="flex h-screen flex-col bg-slate-900 text-slate-100">
      <header className="flex items-center justify-between border-b border-slate-700 px-5 py-3">
        <div className="flex items-center gap-3">
          <h1 className="text-xl font-bold">Mutfak Ekranı</h1>
          <span className="flex items-center gap-1.5 text-xs text-slate-400">
            <span className="h-2 w-2 animate-pulse rounded-full bg-emerald-400" />
            canlı
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => navigate("/staff")}
            className="rounded-lg border border-slate-600 px-3 py-1.5 text-sm text-slate-300 hover:bg-slate-800"
          >
            Panel
          </button>
          <button
            onClick={() => {
              logout();
              navigate("/staff/login", { replace: true });
            }}
            className="rounded-lg border border-slate-600 px-3 py-1.5 text-sm text-slate-300 hover:bg-slate-800"
          >
            Çıkış
          </button>
        </div>
      </header>

      {isLoading ? (
        <div className="flex flex-1 items-center justify-center text-slate-500">Yükleniyor…</div>
      ) : board.length === 0 ? (
        <div className="flex flex-1 flex-col items-center justify-center gap-2 text-slate-500">
          <span className="text-5xl">🍳</span>
          <p className="text-lg">Bekleyen sipariş yok</p>
          <p className="text-sm">Yeni siparişler buraya canlı düşecek.</p>
        </div>
      ) : (
        <div className="grid flex-1 grid-cols-3 gap-3 overflow-hidden p-3">
          {cols.map((col) => {
            const items = board
              .filter((i) => i.kitchen_status === col.key)
              .sort((a, b) => a.opened_at.localeCompare(b.opened_at));
            return (
              <div key={col.key} className="flex min-h-0 flex-col">
                <div className="mb-2 flex items-center justify-between px-1">
                  <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300">
                    {col.title}
                  </h2>
                  <span className="rounded-full bg-slate-700 px-2 py-0.5 text-xs font-semibold">
                    {items.length}
                  </span>
                </div>
                <div className="flex flex-1 flex-col gap-2 overflow-auto pr-1">
                  {items.map((it) => {
                    const mins = elapsedMin(it.opened_at);
                    const late = mins >= 15;
                    return (
                      <button
                        key={it.id}
                        onClick={() =>
                          advance.mutate({ id: it.id, next: NEXT[it.kitchen_status] })
                        }
                        className={[
                          "rounded-xl border-l-4 bg-slate-800 p-3 text-left transition-colors hover:bg-slate-700 active:scale-[0.99]",
                          col.accent,
                          late ? "ring-1 ring-red-500/60" : "",
                        ].join(" ")}
                      >
                        <div className="mb-1 flex items-center justify-between">
                          <span className="rounded bg-slate-700 px-2 py-0.5 text-xs font-semibold text-slate-200">
                            {SOURCE_LABEL[it.source] ?? "Masa"} · {it.table_name ?? "—"}
                          </span>
                          <span
                            className={[
                              "text-xs font-medium",
                              late ? "text-red-400" : "text-slate-400",
                            ].join(" ")}
                          >
                            {mins} dk
                          </span>
                        </div>
                        <div className="flex items-baseline gap-2">
                          <span className="text-lg font-bold text-white">×{it.quantity}</span>
                          <span className="text-lg font-semibold text-slate-100">
                            {it.name_snapshot}
                          </span>
                        </div>
                        {it.note && <p className="mt-1 text-sm text-amber-300">📝 {it.note}</p>}
                        <div className="mt-2 text-right text-xs font-semibold text-slate-400">
                          {col.key === "ready" ? "Servis edildi →" : "İlerlet →"}
                        </div>
                      </button>
                    );
                  })}
                  {items.length === 0 && (
                    <div className="rounded-xl border border-dashed border-slate-700 py-8 text-center text-sm text-slate-600">
                      —
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
