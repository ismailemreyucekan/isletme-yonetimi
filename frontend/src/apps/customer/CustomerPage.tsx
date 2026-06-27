import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { ApiError } from "@shared/api/client";
import { publicApi } from "@shared/api/public";
import type { Order } from "@shared/types";

function money(v: number | string) {
  return `₺${Number(v).toFixed(0)}`;
}

function Icon({ name, className = "" }: { name: string; className?: string }) {
  return <span className={`material-symbols-outlined ${className}`}>{name}</span>;
}

function useTableView(token: string | undefined) {
  return useQuery({
    queryKey: ["public-table", token],
    queryFn: () => publicApi.tableView(token!),
    enabled: !!token,
    refetchInterval: 8000,
  });
}

function Loading() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-cream font-jakarta text-ink-soft">
      Yükleniyor…
    </div>
  );
}

function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-2 bg-cream p-6 text-center font-jakarta">
      <Icon name="error" className="text-4xl text-olive-600" />
      <h1 className="font-serif text-2xl text-ink">Masa bulunamadı</h1>
      <p className="text-sm text-ink-soft">QR kodu geçersiz olabilir. Personele danışın.</p>
    </div>
  );
}

// ── Sayfa 1: Masa menüsü + sipariş (QR doğrudan buraya girer) ─────────────────

export function CustomerPage() {
  const { slug, token } = useParams<{ slug: string; token: string }>();
  const navigate = useNavigate();
  const { data, isLoading, isError } = useTableView(token);

  if (isLoading) return <Loading />;
  if (isError || !data) return <NotFound />;

  const order = data.order;
  const remaining = order ? Number(order.total) - Number(order.paid_total) : 0;

  return (
    <div className="mx-auto min-h-screen max-w-md bg-cream font-jakarta text-ink">
      {/* Üst bar */}
      <header className="fixed top-0 z-50 mx-auto w-full max-w-md border-b border-hairline/40 bg-cream/85 backdrop-blur-xl">
        <div className="flex h-16 items-center justify-between px-5">
          <div className="min-w-0">
            <h1 className="truncate font-serif text-xl font-bold tracking-tight text-olive-700">
              {data.restaurant.name}
            </h1>
            <p className="text-xs font-medium text-ink-soft">{data.table_name}</p>
          </div>
          <button
            onClick={() => navigate(`/r/${slug}/t/${token}/odeme`)}
            className="flex shrink-0 items-center gap-2 rounded-lg bg-olive-600 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-olive-700 active:scale-95"
          >
            <Icon name="receipt_long" className="text-[20px]" />
            <span>Ödeme</span>
            {remaining > 0 && (
              <span className="rounded bg-white/90 px-1.5 py-0.5 text-xs font-bold text-olive-700">
                {money(remaining)}
              </span>
            )}
          </button>
        </div>
      </header>

      <MenuOrder token={token!} />
    </div>
  );
}

// ── Sayfa 2: Ödeme ───────────────────────────────────────────────────────────

export function CustomerPaymentPage() {
  const { slug, token } = useParams<{ slug: string; token: string }>();
  const navigate = useNavigate();
  const { data, isLoading, isError } = useTableView(token);

  if (isLoading) return <Loading />;
  if (isError || !data) return <NotFound />;

  return (
    <div className="mx-auto min-h-screen max-w-md bg-cream font-jakarta text-ink">
      <header className="fixed top-0 z-50 mx-auto w-full max-w-md border-b border-hairline/40 bg-cream/85 backdrop-blur-xl">
        <div className="flex h-16 items-center gap-3 px-5">
          <button
            onClick={() => navigate(`/r/${slug}/t/${token}`)}
            className="flex h-10 w-10 items-center justify-center rounded-lg text-olive-700 transition-colors hover:bg-olive-100 active:scale-95"
            aria-label="Menüye dön"
          >
            <Icon name="arrow_back" className="text-[24px]" />
          </button>
          <div className="min-w-0">
            <h1 className="truncate font-serif text-xl font-bold text-olive-700">Ödeme</h1>
            <p className="text-xs font-medium text-ink-soft">
              {data.restaurant.name} · {data.table_name}
            </p>
          </div>
        </div>
      </header>

      <main className="px-5 pb-32 pt-24">
        <BillPay token={token!} order={data.order} />
      </main>
    </div>
  );
}

// ── Menü + sipariş ───────────────────────────────────────────────────────────

function MenuOrder({ token }: { token: string }) {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ["public-menu", token],
    queryFn: () => publicApi.menu(token),
  });

  const [cart, setCart] = useState<Record<string, number>>({});
  const [activeCat, setActiveCat] = useState<string | null>(null);
  const [toast, setToast] = useState(false);

  const place = useMutation({
    mutationFn: () =>
      publicApi.placeOrder(
        token,
        Object.entries(cart).map(([menu_item_id, quantity]) => ({ menu_item_id, quantity })),
      ),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["public-table", token] });
      setCart({});
      setToast(true);
      window.setTimeout(() => setToast(false), 2500);
    },
  });

  const errorMsg =
    place.error instanceof ApiError ? place.error.message : place.error ? "Hata oluştu" : null;

  if (isLoading) return <div className="pt-24 text-center text-ink-soft">Yükleniyor…</div>;
  if (!data) return null;

  const add = (id: string) => setCart((c) => ({ ...c, [id]: (c[id] ?? 0) + 1 }));
  const sub = (id: string) =>
    setCart((c) => {
      const n = (c[id] ?? 0) - 1;
      const next = { ...c };
      if (n <= 0) delete next[id];
      else next[id] = n;
      return next;
    });

  const priceOf = (id: string) => Number(data.items.find((i) => i.id === id)?.price ?? 0);
  const cartCount = Object.values(cart).reduce((s, q) => s + q, 0);
  const cartTotal = Object.entries(cart).reduce((s, [id, q]) => s + priceOf(id) * q, 0);

  const cats = data.categories.filter((c) => data.items.some((i) => i.category_id === c.id));
  const shownCat = activeCat ?? cats[0]?.id ?? null;
  const visibleItems = data.items.filter((i) => i.category_id === shownCat);

  return (
    <>
      {/* Kategori çipleri (yapışkan) */}
      <nav className="fixed top-16 z-40 mx-auto w-full max-w-md bg-cream/95 backdrop-blur-md">
        <div className="no-scrollbar flex items-center gap-3 overflow-x-auto px-5 py-4">
          {cats.map((c) => (
            <button
              key={c.id}
              onClick={() => setActiveCat(c.id)}
              className={[
                "flex-none rounded-full px-5 py-2.5 text-sm font-semibold transition-all",
                shownCat === c.id
                  ? "bg-olive-600 text-white shadow-[0_4px_20px_-4px_rgba(85,107,47,0.35)]"
                  : "border border-hairline/40 bg-white text-ink-soft hover:border-olive-500/50",
              ].join(" ")}
            >
              {c.name}
            </button>
          ))}
        </div>
      </nav>

      {/* Ürünler */}
      <main className="px-5 pb-32 pt-36">
        <h2 className="mb-6 font-serif text-2xl font-semibold text-ink">
          {cats.find((c) => c.id === shownCat)?.name}
        </h2>

        <section className="space-y-10">
          {visibleItems.map((it) => {
            const qty = cart[it.id] ?? 0;
            return (
              <article key={it.id} className="flex flex-col gap-5">
                {it.image_url ? (
                  <div className="relative aspect-[4/3] w-full overflow-hidden rounded-xl bg-olive-50 shadow-[0_4px_20px_-4px_rgba(85,107,47,0.08)]">
                    <img
                      src={it.image_url}
                      alt={it.name}
                      className="h-full w-full object-cover"
                      onError={(e) => (e.currentTarget.parentElement!.style.display = "none")}
                    />
                    <div className="absolute right-4 top-4 rounded-lg bg-white/90 px-3 py-1 shadow-sm backdrop-blur">
                      <span className="font-jakarta text-lg font-bold text-olive-700">
                        {money(it.price)}
                      </span>
                    </div>
                  </div>
                ) : null}

                <div className="flex items-end justify-between gap-4">
                  <div className="flex-1 space-y-1.5">
                    <h3 className="font-serif text-2xl font-semibold leading-tight text-ink">
                      {it.name}
                    </h3>
                    {it.description && (
                      <p className="max-w-[92%] text-[15px] leading-relaxed text-ink-soft/80">
                        {it.description}
                      </p>
                    )}
                    {!it.image_url && (
                      <p className="font-jakarta text-lg font-bold text-olive-700">
                        {money(it.price)}
                      </p>
                    )}
                  </div>

                  {qty === 0 ? (
                    <button
                      onClick={() => add(it.id)}
                      className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-olive-600 text-white shadow-lg shadow-olive-600/20 transition-all hover:bg-olive-700 active:scale-90"
                      aria-label="Ekle"
                    >
                      <Icon name="add" className="text-[28px]" />
                    </button>
                  ) : (
                    <div className="flex shrink-0 items-center gap-2 rounded-2xl bg-olive-50 p-1">
                      <button
                        onClick={() => sub(it.id)}
                        className="flex h-12 w-12 items-center justify-center rounded-xl bg-white text-olive-700 shadow-sm active:scale-90"
                        aria-label="Azalt"
                      >
                        <Icon name="remove" className="text-[24px]" />
                      </button>
                      <span className="w-6 text-center text-lg font-bold text-olive-700">{qty}</span>
                      <button
                        onClick={() => add(it.id)}
                        className="flex h-12 w-12 items-center justify-center rounded-xl bg-olive-600 text-white shadow-sm active:scale-90"
                        aria-label="Arttır"
                      >
                        <Icon name="add" className="text-[24px]" />
                      </button>
                    </div>
                  )}
                </div>
                <div className="border-b border-hairline/30" />
              </article>
            );
          })}
        </section>
      </main>

      {/* Sipariş onay toast'ı */}
      {toast && (
        <div className="fixed inset-x-0 top-20 z-50 mx-auto flex max-w-md justify-center px-5">
          <div className="flex items-center gap-2 rounded-full bg-olive-600 px-5 py-2.5 text-sm font-semibold text-white shadow-lg">
            <Icon name="check_circle" className="text-[20px]" />
            Siparişiniz alındı
          </div>
        </div>
      )}

      {/* Sepet çubuğu (alt) */}
      {cartCount > 0 && (
        <div className="fixed inset-x-0 bottom-0 z-50 mx-auto max-w-md border-t border-hairline/30 bg-white/95 px-5 pb-7 pt-4 backdrop-blur-xl">
          {errorMsg && (
            <div className="mb-2 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
              {errorMsg}
            </div>
          )}
          <button
            onClick={() => place.mutate()}
            disabled={place.isPending}
            className="flex h-14 w-full items-center justify-between rounded-lg bg-olive-600 px-5 font-semibold text-white transition-colors hover:bg-olive-700 disabled:opacity-60"
          >
            <span className="flex items-center gap-3">
              <span className="flex h-7 min-w-7 items-center justify-center rounded-full bg-white/25 px-1.5 text-sm font-bold">
                {cartCount}
              </span>
              {place.isPending ? "Gönderiliyor…" : "Sipariş Ver"}
            </span>
            <span className="text-lg font-bold">{money(cartTotal)}</span>
          </button>
        </div>
      )}
    </>
  );
}

// ── Hesap + ödeme ────────────────────────────────────────────────────────────

function BillPay({ token, order }: { token: string; order: Order | null }) {
  const [payOpen, setPayOpen] = useState(false);

  if (!order) {
    return (
      <div className="flex flex-col items-center gap-2 py-20 text-center text-ink-soft">
        <Icon name="receipt_long" className="text-5xl text-olive-500/60" />
        <p className="font-serif text-xl text-ink">Henüz açık hesabınız yok</p>
        <p className="text-sm">Menüden sipariş verdiğinizde hesabınız burada görünecek.</p>
      </div>
    );
  }

  const remaining = Number(order.total) - Number(order.paid_total);
  const closed = order.status !== "open" || remaining <= 0;

  return (
    <div>
      {closed && (
        <div className="mb-5 flex flex-col items-center gap-2 rounded-xl border border-olive-200 bg-olive-50 py-8 text-center">
          <Icon name="task_alt" className="text-4xl text-olive-600" />
          <p className="font-serif text-xl font-semibold text-olive-700">
            Tüm hesabınız ödenmiştir
          </p>
          <p className="text-sm text-olive-600">Bizi tercih ettiğiniz için teşekkürler!</p>
        </div>
      )}

      <ul className="overflow-hidden rounded-xl border border-hairline/30 bg-white">
        {order.items.map((it, idx) => {
          const paid = it.paid_status === "paid";
          return (
            <li
              key={it.id}
              className={[
                "flex items-center justify-between px-4 py-3.5",
                idx > 0 ? "border-t border-hairline/20" : "",
                paid ? "opacity-55" : "",
              ].join(" ")}
            >
              <div>
                <p className="font-serif text-lg text-ink">
                  {it.name_snapshot}
                  {paid && (
                    <span className="ml-2 font-jakarta text-xs font-semibold text-olive-600">
                      ✓ ödendi
                    </span>
                  )}
                </p>
                <p className="text-xs text-ink-soft">
                  {it.quantity} × {money(it.unit_price)}
                </p>
                {it.modifiers.length > 0 && (
                  <p className="text-xs text-ink-soft/80">
                    {it.modifiers.map((m) => m.name_snapshot).join(", ")}
                  </p>
                )}
              </div>
              <span className="font-jakarta text-lg font-bold text-ink">{money(it.line_total)}</span>
            </li>
          );
        })}
      </ul>

      <div className="mt-4 rounded-xl border border-hairline/30 bg-white p-4">
        <div className="flex justify-between text-sm text-ink-soft">
          <span>Ara toplam</span>
          <span>{money(order.subtotal)}</span>
        </div>
        {Number(order.discount_amount) > 0 && (
          <div className="mt-1 flex justify-between text-sm text-amber-600">
            <span>İndirim</span>
            <span>−{money(order.discount_amount)}</span>
          </div>
        )}
        {Number(order.service_charge_amount) > 0 && (
          <div className="mt-1 flex justify-between text-sm text-ink-soft">
            <span>Servis ücreti (%{Number(order.service_charge_rate)})</span>
            <span>+{money(order.service_charge_amount)}</span>
          </div>
        )}
        {Number(order.paid_total) > 0 && (
          <div className="mt-1 flex justify-between text-sm text-olive-600">
            <span>Ödenen</span>
            <span>−{money(order.paid_total)}</span>
          </div>
        )}
        <div className="mt-2 flex items-baseline justify-between border-t border-hairline/30 pt-3">
          <span className="font-serif text-lg text-ink">
            {Number(order.paid_total) > 0 ? "Kalan" : "Toplam"}
          </span>
          <span className="font-jakarta text-2xl font-bold text-olive-700">{money(remaining)}</span>
        </div>
      </div>

      {!closed && (
        <button
          onClick={() => setPayOpen(true)}
          className="mt-5 flex h-14 w-full items-center justify-center gap-2 rounded-lg bg-olive-600 font-semibold text-white transition-colors hover:bg-olive-700 active:scale-[0.99]"
        >
          <Icon name="payments" className="text-[22px]" />
          {money(remaining)} Öde
        </button>
      )}

      {payOpen && (
        <PaymentSheet token={token} order={order} onClose={() => setPayOpen(false)} />
      )}
    </div>
  );
}

// ── Ödeme sayfası (bottom sheet) ─────────────────────────────────────────────

type PayMode = "full" | "items" | "split";

function PaymentSheet({
  token,
  order,
  onClose,
}: {
  token: string;
  order: Order;
  onClose: () => void;
}) {
  const qc = useQueryClient();
  const [mode, setMode] = useState<PayMode>("full");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [parts, setParts] = useState(2);
  const [done, setDone] = useState(false);

  const [result, setResult] = useState<Order | null>(null);

  const unpaid = order.items.filter((i) => i.paid_status !== "paid");
  const remaining = Number(order.total) - Number(order.paid_total);
  const selectedTotal = unpaid
    .filter((i) => selected.has(i.id))
    .reduce((s, i) => s + Number(i.line_total), 0);
  // Kişi başı = toplam / kişi (backend ile aynı); son ödemede kalanı geçemez.
  const share = Math.min(Number(order.total) / parts, remaining);

  const pay = useMutation({
    mutationFn: () => {
      if (mode === "full") return publicApi.payFull(token);
      if (mode === "items") return publicApi.payItems(token, [...selected]);
      return publicApi.paySplit(token, parts);
    },
    onSuccess: (o) => {
      qc.setQueryData(["public-table", token], (prev: unknown) =>
        prev ? { ...(prev as object), order: o } : prev,
      );
      qc.invalidateQueries({ queryKey: ["public-table", token] });
      setResult(o);
      setDone(true);
    },
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
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/40">
      <div className="mx-auto flex max-h-[90vh] w-full max-w-md flex-col rounded-t-3xl bg-cream">
        <div className="flex items-center justify-between border-b border-hairline/30 px-5 py-4">
          <h3 className="font-serif text-xl font-semibold text-ink">
            {done ? "Ödeme alındı" : "Ödeme"}
          </h3>
          <button onClick={onClose} className="text-ink-soft">
            <Icon name="close" className="text-[24px]" />
          </button>
        </div>

        {done ? (
          (() => {
            const newRemaining = result
              ? Number(result.total) - Number(result.paid_total)
              : 0;
            const fullyPaid = !result || result.status !== "open" || newRemaining <= 0.001;
            return (
              <div className="flex flex-col items-center gap-3 px-6 py-10 text-center">
                <Icon
                  name={fullyPaid ? "celebration" : "check_circle"}
                  className="text-5xl text-olive-600"
                />
                {fullyPaid ? (
                  <>
                    <p className="font-serif text-2xl font-semibold text-ink">Teşekkürler!</p>
                    <p className="text-sm text-ink-soft">Tüm hesap ödendi.</p>
                  </>
                ) : (
                  <>
                    <p className="font-serif text-2xl font-semibold text-ink">
                      Payınız alındı
                    </p>
                    <p className="text-sm text-ink-soft">
                      Bu masada hâlâ{" "}
                      <span className="font-bold text-olive-700">{money(newRemaining)}</span>{" "}
                      ödenmemiş tutar var.
                    </p>
                  </>
                )}
                <div className="mt-2 flex gap-2">
                  {!fullyPaid && (
                    <button
                      onClick={() => {
                        setDone(false);
                        setResult(null);
                        setSelected(new Set());
                      }}
                      className="rounded-lg border border-olive-600 px-5 py-3 font-semibold text-olive-700"
                    >
                      Kalanı Öde
                    </button>
                  )}
                  <button
                    onClick={onClose}
                    className="rounded-lg bg-olive-600 px-6 py-3 font-semibold text-white"
                  >
                    Kapat
                  </button>
                </div>
              </div>
            );
          })()
        ) : (
          <>
            <div className="grid grid-cols-3 gap-2 p-4">
              {(
                [
                  ["full", "Tüm Hesap"],
                  ["items", "Yediğim"],
                  ["split", "Kişiye Böl"],
                ] as const
              ).map(([m, label]) => (
                <button
                  key={m}
                  onClick={() => setMode(m)}
                  className={[
                    "rounded-lg py-2.5 text-sm font-semibold transition-colors",
                    mode === m
                      ? "bg-olive-600 text-white"
                      : "border border-hairline/40 bg-white text-ink-soft",
                  ].join(" ")}
                >
                  {label}
                </button>
              ))}
            </div>

            <div className="flex-1 overflow-auto px-5">
              {mode === "full" && (
                <p className="py-4 text-sm text-ink-soft">
                  Kalan tutarın tamamı ({money(remaining)}) ödenecek.
                </p>
              )}

              {mode === "items" && (
                <div className="py-2">
                  <p className="mb-2 text-sm text-ink-soft">Ödeyeceğiniz ürünleri seçin:</p>
                  <ul className="flex flex-col gap-2">
                    {unpaid.map((it) => (
                      <li key={it.id}>
                        <label className="flex cursor-pointer items-center gap-3 rounded-lg border border-hairline/40 bg-white p-3">
                          <input
                            type="checkbox"
                            checked={selected.has(it.id)}
                            onChange={() => toggle(it.id)}
                            className="h-5 w-5 accent-olive-600"
                          />
                          <span className="flex-1 font-serif text-ink">
                            {it.name_snapshot} ×{it.quantity}
                          </span>
                          <span className="font-jakarta font-semibold">{money(it.line_total)}</span>
                        </label>
                      </li>
                    ))}
                  </ul>
                  <p className="mt-3 text-right font-semibold text-olive-700">
                    Seçili: {money(selectedTotal)}
                  </p>
                </div>
              )}

              {mode === "split" && (
                <div className="py-4">
                  <label className="text-sm text-ink-soft">Kaç kişi bölüşüyor?</label>
                  <div className="mt-2 flex items-center justify-center gap-4">
                    <button
                      onClick={() => setParts((p) => Math.max(2, p - 1))}
                      className="flex h-12 w-12 items-center justify-center rounded-xl bg-white text-olive-700 shadow-sm"
                    >
                      <Icon name="remove" className="text-[24px]" />
                    </button>
                    <span className="w-12 text-center font-jakarta text-3xl font-bold text-olive-700">
                      {parts}
                    </span>
                    <button
                      onClick={() => setParts((p) => p + 1)}
                      className="flex h-12 w-12 items-center justify-center rounded-xl bg-olive-600 text-white shadow-sm"
                    >
                      <Icon name="add" className="text-[24px]" />
                    </button>
                  </div>
                  <p className="mt-4 text-center text-ink-soft">
                    Kişi başı: <span className="font-bold text-olive-700">{money(share)}</span>
                  </p>
                  <p className="mt-1 text-center text-xs text-ink-soft/70">
                    Bu ekrandan 1 kişilik pay ödenir. Herkes kendi telefonundan ödeyebilir.
                  </p>
                </div>
              )}
            </div>

            <div className="border-t border-hairline/30 p-4">
              {errorMsg && (
                <div className="mb-2 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
                  {errorMsg}
                </div>
              )}
              <button
                onClick={() => pay.mutate()}
                disabled={pay.isPending || (mode === "items" && selected.size === 0)}
                className="h-14 w-full rounded-lg bg-olive-600 font-semibold text-white transition-colors hover:bg-olive-700 disabled:opacity-60"
              >
                {pay.isPending
                  ? "İşleniyor…"
                  : mode === "split"
                    ? `${money(share)} Öde`
                    : mode === "items"
                      ? `${money(selectedTotal)} Öde`
                      : `${money(remaining)} Öde`}
              </button>
              <p className="mt-2 text-center text-xs text-ink-soft/70">
                🔒 Güvenli online ödeme (demo)
              </p>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
