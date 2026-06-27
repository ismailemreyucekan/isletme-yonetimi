import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { menuApi } from "@shared/api/menu";
import { type ModifierGroup, modifiersApi } from "@shared/api/modifiers";
import { ordersApi } from "@shared/api/pos";
import { ApiError } from "@shared/api/client";
import type { Order } from "@shared/types";
import { Button } from "@shared/ui/Button";

function money(v: number | string) {
  return `₺${Number(v).toFixed(2)}`;
}

export function PosOrderPage() {
  const { orderId } = useParams<{ orderId: string }>();
  const navigate = useNavigate();
  const qc = useQueryClient();

  const [activeCat, setActiveCat] = useState<string | null>(null);
  const [payOpen, setPayOpen] = useState(false);
  const [discountOpen, setDiscountOpen] = useState(false);
  const [scOpen, setScOpen] = useState(false);

  const { data: categories = [] } = useQuery({
    queryKey: ["menu-categories"],
    queryFn: menuApi.listCategories,
  });
  const { data: items = [] } = useQuery({
    queryKey: ["menu-items"],
    queryFn: menuApi.listItems,
  });
  const { data: order } = useQuery({
    queryKey: ["order", orderId],
    queryFn: () => ordersApi.get(orderId!),
    enabled: !!orderId,
    // Müşteri QR'dan sipariş verdiğinde personel ekranı canlı güncellensin.
    refetchInterval: 5000,
  });

  const setOrder = (o: Order) => qc.setQueryData(["order", orderId], o);

  const addItem = useMutation({
    mutationFn: (vars: { menuItemId: string; modifierIds?: string[] }) =>
      ordersApi.addItem(orderId!, vars.menuItemId, 1, undefined, vars.modifierIds ?? []),
    onSuccess: setOrder,
  });
  const [modItem, setModItem] = useState<{ id: string; name: string; groups: ModifierGroup[] } | null>(
    null,
  );

  const handleItemClick = async (it: { id: string; name: string }) => {
    const groups = await modifiersApi.itemGroups(it.id);
    if (groups.length === 0) addItem.mutate({ menuItemId: it.id });
    else setModItem({ id: it.id, name: it.name, groups });
  };
  const updateItem = useMutation({
    mutationFn: ({ id, qty }: { id: string; qty: number }) =>
      ordersApi.updateItem(orderId!, id, qty),
    onSuccess: setOrder,
  });
  const removeItem = useMutation({
    mutationFn: (id: string) => ordersApi.removeItem(orderId!, id),
    onSuccess: setOrder,
  });
  const discount = useMutation({
    mutationFn: ({ mode, value }: { mode: "percent" | "amount"; value: number }) =>
      ordersApi.setDiscount(orderId!, mode, value),
    onSuccess: (o) => {
      setOrder(o);
      setDiscountOpen(false);
    },
  });
  const serviceCharge = useMutation({
    mutationFn: (rate: number) => ordersApi.setServiceCharge(orderId!, rate),
    onSuccess: (o) => {
      setOrder(o);
      setScOpen(false);
    },
  });
  const couponApply = useMutation({
    mutationFn: (code: string) => ordersApi.applyCoupon(orderId!, code),
    onSuccess: (o) => {
      setOrder(o);
      setDiscountOpen(false);
    },
  });

  const visibleCats = categories.filter((c) => c.is_active);
  const shownCat = activeCat ?? visibleCats[0]?.id ?? null;
  const visibleItems = useMemo(
    () => items.filter((i) => i.is_available && i.category_id === shownCat),
    [items, shownCat],
  );

  const remaining = order
    ? Number(order.total) - Number(order.paid_total)
    : 0;

  const goBack = () => {
    qc.invalidateQueries({ queryKey: ["tables"] });
    navigate("/staff/tables");
  };

  if (!order) return <div className="p-8 text-slate-500">Yükleniyor…</div>;

  return (
    <div className="flex h-screen">
      {/* Sol + orta: menü */}
      <div className="flex flex-1 flex-col overflow-hidden">
        <div className="flex items-center gap-3 border-b bg-white px-4 py-2">
          <button onClick={goBack} className="text-sm text-slate-500 hover:text-slate-800">
            ← Masalar
          </button>
          <div className="flex gap-1 overflow-x-auto">
            {visibleCats.map((c) => (
              <button
                key={c.id}
                onClick={() => setActiveCat(c.id)}
                className={[
                  "whitespace-nowrap rounded-lg px-3 py-1.5 text-sm font-medium transition-colors",
                  shownCat === c.id
                    ? "bg-brand-600 text-white"
                    : "bg-slate-100 text-slate-600 hover:bg-slate-200",
                ].join(" ")}
              >
                {c.name}
              </button>
            ))}
          </div>
        </div>

        <div className="grid flex-1 grid-cols-2 gap-2 overflow-auto p-3 sm:grid-cols-3 lg:grid-cols-4">
          {visibleItems.map((item) => (
            <button
              key={item.id}
              onClick={() => handleItemClick(item)}
              className="flex flex-col items-center justify-center gap-1 rounded-xl border border-slate-200 bg-white p-3 text-center shadow-sm transition-all hover:border-brand-400 hover:shadow active:scale-95"
            >
              <span className="text-sm font-medium leading-tight text-slate-800">
                {item.name}
              </span>
              <span className="text-sm font-bold text-brand-700">{money(item.price)}</span>
            </button>
          ))}
          {visibleItems.length === 0 && (
            <p className="col-span-full py-8 text-center text-slate-400">
              Bu kategoride ürün yok.
            </p>
          )}
        </div>
      </div>

      {/* Sağ: adisyon */}
      <div className="flex w-80 shrink-0 flex-col border-l bg-white">
        <div className="border-b px-4 py-3">
          <div className="flex items-center gap-2">
            <h2 className="font-semibold text-slate-800">Adisyon</h2>
            {order.source === "qr_self_order" && (
              <span className="rounded-full bg-brand-100 px-2 py-0.5 text-xs font-medium text-brand-700">
                📱 QR Sipariş
              </span>
            )}
          </div>
          {order.status !== "open" && (
            <span className="text-xs font-medium text-emerald-600">Ödendi / Kapandı</span>
          )}
        </div>

        <div className="flex-1 overflow-auto p-3">
          {order.items.length === 0 ? (
            <p className="py-8 text-center text-sm text-slate-400">
              Soldaki menüden ürün ekleyin.
            </p>
          ) : (
            <ul className="flex flex-col gap-2">
              {order.items.map((it) => {
                const paid = it.paid_status === "paid";
                return (
                  <li
                    key={it.id}
                    className={[
                      "rounded-lg border p-2",
                      paid ? "border-emerald-200 bg-emerald-50 opacity-70" : "border-slate-200",
                    ].join(" ")}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <span className="text-sm font-medium text-slate-800">
                        {it.name_snapshot}
                        {paid && <span className="ml-1 text-xs text-emerald-600">✓ ödendi</span>}
                      </span>
                      <span className="text-sm font-semibold text-slate-900">
                        {money(it.line_total)}
                      </span>
                    </div>
                    {it.modifiers.length > 0 && (
                      <p className="mt-0.5 text-xs text-slate-500">
                        {it.modifiers.map((m) => m.name_snapshot).join(", ")}
                      </p>
                    )}
                    {!paid && order.status === "open" && (
                      <div className="mt-1 flex items-center gap-2">
                        <button
                          onClick={() =>
                            it.quantity > 1
                              ? updateItem.mutate({ id: it.id, qty: it.quantity - 1 })
                              : removeItem.mutate(it.id)
                          }
                          className="h-6 w-6 rounded bg-slate-100 text-slate-700 hover:bg-slate-200"
                        >
                          −
                        </button>
                        <span className="w-6 text-center text-sm">{it.quantity}</span>
                        <button
                          onClick={() => updateItem.mutate({ id: it.id, qty: it.quantity + 1 })}
                          className="h-6 w-6 rounded bg-slate-100 text-slate-700 hover:bg-slate-200"
                        >
                          +
                        </button>
                        <span className="ml-auto text-xs text-slate-400">
                          {money(it.unit_price)}/adet
                        </span>
                        <button
                          onClick={() => removeItem.mutate(it.id)}
                          className="text-xs text-red-500 hover:underline"
                        >
                          sil
                        </button>
                      </div>
                    )}
                    {paid && <div className="mt-0.5 text-xs text-slate-400">{it.quantity} adet</div>}
                  </li>
                );
              })}
            </ul>
          )}
        </div>

        <div className="border-t p-4">
          <div className="mb-1 flex justify-between text-sm text-slate-500">
            <span>Ara toplam</span>
            <span>{money(order.subtotal)}</span>
          </div>
          {Number(order.discount_amount) > 0 && (
            <div className="mb-1 flex justify-between text-sm text-amber-600">
              <span>İndirim</span>
              <span>−{money(order.discount_amount)}</span>
            </div>
          )}
          {Number(order.service_charge_amount) > 0 && (
            <div className="mb-1 flex justify-between text-sm text-slate-500">
              <span>Servis ücreti (%{Number(order.service_charge_rate)})</span>
              <span>+{money(order.service_charge_amount)}</span>
            </div>
          )}
          {Number(order.paid_total) > 0 && (
            <div className="mb-1 flex justify-between text-sm text-emerald-600">
              <span>Ödenen</span>
              <span>−{money(order.paid_total)}</span>
            </div>
          )}
          <div className="mb-3 flex justify-between text-lg font-bold text-slate-900">
            <span>{Number(order.paid_total) > 0 ? "Kalan" : "Toplam"}</span>
            <span>{money(remaining)}</span>
          </div>

          {order.status === "open" ? (
            <div className="flex flex-col gap-2">
              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={() => setDiscountOpen(true)}
                  disabled={order.items.length === 0}
                  className="rounded-lg border border-slate-300 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {Number(order.discount_amount) > 0 ? "İndirim ✓" : "İndirim"}
                </button>
                <button
                  onClick={() => setScOpen(true)}
                  disabled={order.items.length === 0}
                  className="rounded-lg border border-slate-300 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {Number(order.service_charge_amount) > 0 ? "Servis ✓" : "Servis Ücreti"}
                </button>
              </div>
              <Button
                className="w-full"
                disabled={order.items.length === 0 || remaining <= 0}
                onClick={() => setPayOpen(true)}
              >
                Ödeme Al
              </Button>
            </div>
          ) : (
            <Button className="w-full" onClick={goBack}>
              Masalara Dön
            </Button>
          )}
        </div>
      </div>

      {payOpen && (
        <PaymentModal
          order={order}
          onClose={() => setPayOpen(false)}
          onPaid={(o) => {
            setOrder(o);
            if (o.status !== "open") {
              setPayOpen(false);
              goBack();
            } else {
              setPayOpen(false);
            }
          }}
        />
      )}

      {discountOpen && (
        <DiscountModal
          order={order}
          pending={discount.isPending}
          error={discount.error}
          couponPending={couponApply.isPending}
          couponError={couponApply.error}
          onClose={() => setDiscountOpen(false)}
          onApply={(mode, value) => discount.mutate({ mode, value })}
          onApplyCoupon={(code) => couponApply.mutate(code)}
        />
      )}

      {scOpen && (
        <ServiceChargeModal
          order={order}
          pending={serviceCharge.isPending}
          error={serviceCharge.error}
          onClose={() => setScOpen(false)}
          onApply={(rate) => serviceCharge.mutate(rate)}
        />
      )}

      {modItem && (
        <ModifierSelectModal
          itemName={modItem.name}
          groups={modItem.groups}
          pending={addItem.isPending}
          onClose={() => setModItem(null)}
          onConfirm={(ids) =>
            addItem.mutate(
              { menuItemId: modItem.id, modifierIds: ids },
              { onSuccess: () => setModItem(null) },
            )
          }
        />
      )}
    </div>
  );
}

// ── Opsiyon Seçim Modalı ─────────────────────────────────────────────────────

function ModifierSelectModal({
  itemName,
  groups,
  pending,
  onClose,
  onConfirm,
}: {
  itemName: string;
  groups: ModifierGroup[];
  pending: boolean;
  onClose: () => void;
  onConfirm: (modifierIds: string[]) => void;
}) {
  const [selected, setSelected] = useState<Record<string, Set<string>>>({});
  const getSel = (gid: string) => selected[gid] ?? new Set<string>();
  const setSel = (gid: string, next: Set<string>) =>
    setSelected((s) => ({ ...s, [gid]: next }));

  const pickSingle = (gid: string, mid: string) => setSel(gid, new Set([mid]));
  const toggleMulti = (g: ModifierGroup, mid: string) => {
    const cur = new Set(getSel(g.id));
    if (cur.has(mid)) cur.delete(mid);
    else if (cur.size < g.max_select) cur.add(mid);
    setSel(g.id, cur);
  };

  const valid = groups.every((g) => {
    const n = getSel(g.id).size;
    if (g.is_required && n < Math.max(g.min_select, 1)) return false;
    return n >= g.min_select;
  });

  const allIds = Object.values(selected).flatMap((s) => [...s]);
  const extra = groups
    .flatMap((g) => g.modifiers.filter((m) => getSel(g.id).has(m.id)))
    .reduce((sum, m) => sum + Number(m.price_delta), 0);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="flex max-h-[90vh] w-full max-w-md flex-col rounded-2xl bg-white shadow-xl">
        <div className="flex items-center justify-between border-b px-5 py-3">
          <h3 className="font-semibold text-slate-800">{itemName} — Seçenekler</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-700">
            ✕
          </button>
        </div>

        <div className="flex-1 space-y-4 overflow-auto p-5">
          {groups.map((g) => (
            <div key={g.id}>
              <div className="mb-1 flex items-center justify-between">
                <span className="text-sm font-semibold text-slate-700">{g.name}</span>
                <span className="text-xs text-slate-400">
                  {g.is_required ? "zorunlu" : "opsiyonel"}
                  {g.selection_type === "multiple" && ` · en fazla ${g.max_select}`}
                </span>
              </div>
              <div className="space-y-1">
                {g.modifiers
                  .filter((m) => m.is_available)
                  .map((m) => {
                    const checked = getSel(g.id).has(m.id);
                    return (
                      <label
                        key={m.id}
                        className={[
                          "flex cursor-pointer items-center gap-2 rounded-lg border p-2 text-sm",
                          checked ? "border-brand-400 bg-brand-50" : "border-slate-200",
                        ].join(" ")}
                      >
                        <input
                          type={g.selection_type === "single" ? "radio" : "checkbox"}
                          name={g.id}
                          checked={checked}
                          onChange={() =>
                            g.selection_type === "single"
                              ? pickSingle(g.id, m.id)
                              : toggleMulti(g, m.id)
                          }
                          className="h-4 w-4"
                        />
                        <span className="flex-1 text-slate-700">{m.name}</span>
                        {Number(m.price_delta) !== 0 && (
                          <span className="text-slate-500">+₺{Number(m.price_delta)}</span>
                        )}
                      </label>
                    );
                  })}
              </div>
            </div>
          ))}
        </div>

        <div className="border-t p-4">
          <Button
            className="w-full"
            loading={pending}
            disabled={!valid}
            onClick={() => onConfirm(allIds)}
          >
            Sepete Ekle{extra > 0 ? ` (+${money(extra)})` : ""}
          </Button>
        </div>
      </div>
    </div>
  );
}

// ── Servis Ücreti Modalı ─────────────────────────────────────────────────────

function ServiceChargeModal({
  order,
  pending,
  error,
  onClose,
  onApply,
}: {
  order: Order;
  pending: boolean;
  error: unknown;
  onClose: () => void;
  onApply: (rate: number) => void;
}) {
  const [rate, setRate] = useState(
    Number(order.service_charge_rate) > 0 ? String(Number(order.service_charge_rate)) : "",
  );

  const subtotal = Number(order.subtotal);
  const num = Number(rate) || 0;
  const applied = (subtotal * num) / 100;
  const errorMsg =
    error instanceof ApiError ? error.message : error ? "Hata oluştu" : null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-sm rounded-2xl bg-white shadow-xl">
        <div className="flex items-center justify-between border-b px-5 py-3">
          <h3 className="font-semibold text-slate-800">Servis Ücreti</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-700">
            ✕
          </button>
        </div>

        <div className="p-5">
          <label className="text-sm text-slate-600">Oran (%)</label>
          <div className="mt-1 flex items-center gap-2">
            {[5, 10, 15].map((r) => (
              <button
                key={r}
                onClick={() => setRate(String(r))}
                className={[
                  "flex-1 rounded-lg border py-2 text-sm font-medium",
                  num === r
                    ? "border-brand-600 bg-brand-50 text-brand-700"
                    : "border-slate-200 text-slate-600",
                ].join(" ")}
              >
                %{r}
              </button>
            ))}
          </div>
          <input
            type="number"
            inputMode="decimal"
            value={rate}
            onChange={(e) => setRate(e.target.value)}
            placeholder="örn. 10"
            min={0}
            max={100}
            className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
          />

          <p className="mt-2 text-sm text-slate-500">
            Eklenecek servis ücreti:{" "}
            <span className="font-semibold text-slate-700">+{money(applied)}</span>
          </p>

          {errorMsg && (
            <div className="mt-2 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
              {errorMsg}
            </div>
          )}
        </div>

        <div className="flex gap-2 border-t p-4">
          {Number(order.service_charge_amount) > 0 && (
            <Button variant="secondary" disabled={pending} onClick={() => onApply(0)}>
              Kaldır
            </Button>
          )}
          <Button
            className="flex-1"
            loading={pending}
            disabled={num <= 0}
            onClick={() => onApply(num)}
          >
            Uygula
          </Button>
        </div>
      </div>
    </div>
  );
}

// ── İndirim Modalı ───────────────────────────────────────────────────────────

function DiscountModal({
  order,
  pending,
  error,
  couponPending,
  couponError,
  onClose,
  onApply,
  onApplyCoupon,
}: {
  order: Order;
  pending: boolean;
  error: unknown;
  couponPending: boolean;
  couponError: unknown;
  onClose: () => void;
  onApply: (mode: "percent" | "amount", value: number) => void;
  onApplyCoupon: (code: string) => void;
}) {
  const [mode, setMode] = useState<"percent" | "amount">("percent");
  const [value, setValue] = useState("");
  const [coupon, setCoupon] = useState("");

  const subtotal = Number(order.subtotal);
  const num = Number(value) || 0;
  const applied =
    mode === "percent"
      ? Math.min((subtotal * num) / 100, subtotal)
      : Math.min(num, subtotal);
  const errorMsg =
    error instanceof ApiError ? error.message : error ? "Hata oluştu" : null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-sm rounded-2xl bg-white shadow-xl">
        <div className="flex items-center justify-between border-b px-5 py-3">
          <h3 className="font-semibold text-slate-800">İndirim</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-700">
            ✕
          </button>
        </div>

        <div className="p-5">
          {/* Kupon kodu */}
          <div className="mb-4 border-b border-slate-100 pb-4">
            <label className="text-sm font-medium text-slate-700">Kupon kodu</label>
            <div className="mt-1 flex gap-2">
              <input
                value={coupon}
                onChange={(e) => setCoupon(e.target.value.toUpperCase())}
                placeholder="ÖRN. INDIRIM10"
                className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm uppercase focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
              <Button
                variant="secondary"
                loading={couponPending}
                disabled={!coupon.trim()}
                onClick={() => onApplyCoupon(coupon.trim())}
              >
                Uygula
              </Button>
            </div>
            {couponError instanceof ApiError && (
              <p className="mt-1 text-xs text-red-600">{couponError.message}</p>
            )}
          </div>

          <p className="mb-2 text-sm font-medium text-slate-700">Manuel indirim</p>
          <div className="mb-3 grid grid-cols-2 gap-1 rounded-lg bg-slate-100 p-1">
            {(
              [
                ["percent", "Yüzde %"],
                ["amount", "Tutar ₺"],
              ] as const
            ).map(([m, label]) => (
              <button
                key={m}
                onClick={() => setMode(m)}
                className={[
                  "rounded-md py-2 text-sm font-medium transition-colors",
                  mode === m ? "bg-white text-brand-700 shadow-sm" : "text-slate-500",
                ].join(" ")}
              >
                {label}
              </button>
            ))}
          </div>

          <input
            type="number"
            inputMode="decimal"
            autoFocus
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder={mode === "percent" ? "örn. 10" : "örn. 50"}
            min={0}
            max={mode === "percent" ? 100 : undefined}
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
          />

          <p className="mt-2 text-sm text-slate-500">
            İndirim:{" "}
            <span className="font-semibold text-amber-600">−{money(applied)}</span> → yeni
            toplam {money(Math.max(0, subtotal - applied))}
          </p>

          {errorMsg && (
            <div className="mt-2 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
              {errorMsg}
            </div>
          )}
        </div>

        <div className="flex gap-2 border-t p-4">
          {Number(order.discount_amount) > 0 && (
            <Button
              variant="secondary"
              disabled={pending}
              onClick={() => onApply("amount", 0)}
            >
              Kaldır
            </Button>
          )}
          <Button
            className="flex-1"
            loading={pending}
            disabled={num <= 0}
            onClick={() => onApply(mode, num)}
          >
            Uygula
          </Button>
        </div>
      </div>
    </div>
  );
}

// ── Ödeme Modalı ───────────────────────────────────────────────────────────

type PayMode = "full" | "items" | "split";

function PaymentModal({
  order,
  onClose,
  onPaid,
}: {
  order: Order;
  onClose: () => void;
  onPaid: (o: Order) => void;
}) {
  const [mode, setMode] = useState<PayMode>("full");
  const [method, setMethod] = useState<"cash" | "card">("cash");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [parts, setParts] = useState(2);

  const unpaid = order.items.filter((i) => i.paid_status !== "paid");
  const remaining = Number(order.total) - Number(order.paid_total);
  const selectedTotal = unpaid
    .filter((i) => selected.has(i.id))
    .reduce((s, i) => s + Number(i.line_total), 0);
  const share = remaining / parts;

  // Servis ücreti/indirim dahil seçili kalemlerin gerçek tahsilatı (backend ile aynı).
  const subtotal = Number(order.subtotal);
  const total = Number(order.total);
  const selectionClosesAll = unpaid.length > 0 && unpaid.every((i) => selected.has(i.id));
  const selectedCharge =
    selected.size === 0
      ? 0
      : selectionClosesAll
        ? remaining
        : subtotal > 0
          ? (selectedTotal * total) / subtotal
          : selectedTotal;

  const [tip, setTip] = useState(0);
  const tipBase = mode === "full" ? remaining : mode === "items" ? selectedCharge : share;

  const pay = useMutation({
    mutationFn: () => {
      if (mode === "full") return ordersApi.payFull(order.id, method, tip);
      if (mode === "items") return ordersApi.payItems(order.id, [...selected], method, tip);
      return ordersApi.paySplit(order.id, parts, method, tip);
    },
    onSuccess: onPaid,
  });

  const errorMsg =
    pay.error instanceof ApiError ? pay.error.message : pay.error ? "Hata oluştu" : null;

  const toggle = (id: string) =>
    setSelected((s) => {
      const n = new Set(s);
      if (n.has(id)) n.delete(id);
      else n.add(id);
      return n;
    });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="flex max-h-[90vh] w-full max-w-md flex-col rounded-2xl bg-white shadow-xl">
        <div className="flex items-center justify-between border-b px-5 py-3">
          <h3 className="font-semibold text-slate-800">Ödeme — Kalan {money(remaining)}</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-700">
            ✕
          </button>
        </div>

        <div className="grid grid-cols-3 gap-1 p-3">
          {(
            [
              ["full", "Tüm Hesap"],
              ["items", "Ürün Seç"],
              ["split", "Kişiye Böl"],
            ] as const
          ).map(([m, label]) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={[
                "rounded-lg py-2 text-sm font-medium transition-colors",
                mode === m ? "bg-brand-600 text-white" : "bg-slate-100 text-slate-600",
              ].join(" ")}
            >
              {label}
            </button>
          ))}
        </div>

        <div className="flex-1 overflow-auto px-5">
          {mode === "full" && (
            <p className="py-4 text-sm text-slate-600">
              Kalan tutarın tamamı ({money(remaining)}) tahsil edilecek ve hesap kapanacak.
            </p>
          )}

          {mode === "items" && (
            <div className="py-2">
              <p className="mb-2 text-sm text-slate-500">Ödenecek ürünleri seçin:</p>
              <ul className="flex flex-col gap-1">
                {unpaid.map((it) => (
                  <li key={it.id}>
                    <label className="flex cursor-pointer items-center gap-2 rounded-lg border border-slate-200 p-2">
                      <input
                        type="checkbox"
                        checked={selected.has(it.id)}
                        onChange={() => toggle(it.id)}
                        className="h-4 w-4"
                      />
                      <span className="flex-1 text-sm text-slate-700">
                        {it.name_snapshot} ×{it.quantity}
                      </span>
                      <span className="text-sm font-medium">{money(it.line_total)}</span>
                    </label>
                  </li>
                ))}
              </ul>
              <p className="mt-3 text-right text-sm font-semibold">
                Tahsil edilecek: {money(selectedCharge)}
              </p>
              {Number(order.service_charge_amount) > 0 && selected.size > 0 && (
                <p className="text-right text-xs text-slate-400">servis ücreti dahil</p>
              )}
            </div>
          )}

          {mode === "split" && (
            <div className="py-4">
              <label className="text-sm text-slate-600">Kişi sayısı</label>
              <div className="mt-2 flex items-center gap-3">
                <button
                  onClick={() => setParts((p) => Math.max(2, p - 1))}
                  className="h-9 w-9 rounded-lg bg-slate-100 text-lg"
                >
                  −
                </button>
                <span className="w-10 text-center text-lg font-semibold">{parts}</span>
                <button
                  onClick={() => setParts((p) => p + 1)}
                  className="h-9 w-9 rounded-lg bg-slate-100 text-lg"
                >
                  +
                </button>
              </div>
              <p className="mt-3 text-sm text-slate-600">
                Kişi başı: <span className="font-semibold">{money(share)}</span>
              </p>
              <p className="mt-1 text-xs text-slate-400">
                Her "Öde" bir kişinin payını ({money(share)}) tahsil eder. Tümü ödenince hesap kapanır.
              </p>
            </div>
          )}
        </div>

        <div className="border-t p-4">
          {/* Bahşiş (opsiyonel) */}
          <div className="mb-3">
            <div className="mb-1 flex items-center justify-between">
              <span className="text-sm text-slate-600">Bahşiş</span>
              {tip > 0 && (
                <span className="text-sm font-semibold text-emerald-600">+{money(tip)}</span>
              )}
            </div>
            <div className="flex gap-1">
              {[0, 5, 10, 15].map((pct) => {
                const val = pct === 0 ? 0 : Math.round(tipBase * pct) / 100;
                return (
                  <button
                    key={pct}
                    onClick={() => setTip(val)}
                    className="flex-1 rounded-lg border border-slate-200 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50"
                  >
                    {pct === 0 ? "Yok" : `%${pct}`}
                  </button>
                );
              })}
              <input
                type="number"
                inputMode="decimal"
                value={tip || ""}
                onChange={(e) => setTip(Math.max(0, Number(e.target.value) || 0))}
                placeholder="₺"
                min={0}
                className="w-16 rounded-lg border border-slate-200 px-2 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>
          </div>

          <div className="mb-3 flex gap-2">
            {(["cash", "card"] as const).map((m) => (
              <button
                key={m}
                onClick={() => setMethod(m)}
                className={[
                  "flex-1 rounded-lg border py-2 text-sm font-medium",
                  method === m
                    ? "border-brand-600 bg-brand-50 text-brand-700"
                    : "border-slate-200 text-slate-600",
                ].join(" ")}
              >
                {m === "cash" ? "💵 Nakit" : "💳 Kart"}
              </button>
            ))}
          </div>

          {errorMsg && (
            <div className="mb-2 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
              {errorMsg}
            </div>
          )}

          <Button
            className="w-full"
            loading={pay.isPending}
            disabled={mode === "items" && selected.size === 0}
            onClick={() => pay.mutate()}
          >
            {mode === "split"
              ? `${money(share + tip)} Öde (1 kişi)`
              : mode === "items"
                ? `${money(selectedCharge + tip)} Öde`
                : `${money(remaining + tip)} Öde`}
          </Button>
        </div>
      </div>
    </div>
  );
}
