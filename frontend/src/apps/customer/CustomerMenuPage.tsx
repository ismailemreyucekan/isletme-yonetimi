import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useParams } from "react-router-dom";

import { publicApi } from "@shared/api/public";

function money(v: number | string) {
  return `₺${Number(v).toFixed(0)}`;
}

function Icon({ name, className = "" }: { name: string; className?: string }) {
  return <span className={`material-symbols-outlined ${className}`}>{name}</span>;
}

export function CustomerMenuPage() {
  const { slug } = useParams<{ slug: string }>();
  const [activeCat, setActiveCat] = useState<string | null>(null);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["public-menu-slug", slug],
    queryFn: () => publicApi.menuBySlug(slug!),
    enabled: !!slug,
  });

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-cream font-jakarta text-ink-soft">
        Yükleniyor…
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-2 bg-cream p-6 text-center font-jakarta">
        <Icon name="error" className="text-4xl text-olive-600" />
        <h1 className="font-serif text-2xl text-ink">İşletme bulunamadı</h1>
      </div>
    );
  }

  const cats = data.categories.filter((c) => data.items.some((i) => i.category_id === c.id));
  const shownCat = activeCat ?? cats[0]?.id ?? null;
  const visibleItems = data.items.filter((i) => i.category_id === shownCat);

  return (
    <div className="mx-auto min-h-screen max-w-md bg-cream font-jakarta text-ink">
      {/* Üst bar */}
      <header className="fixed top-0 z-50 mx-auto w-full max-w-md border-b border-hairline/40 bg-cream/85 backdrop-blur-xl">
        <div className="flex h-16 items-center justify-center px-5">
          <h1 className="font-serif text-2xl font-bold tracking-tight text-olive-700">
            {data.restaurant.name}
          </h1>
        </div>
      </header>

      {/* Kategori çipleri */}
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

      <main className="px-5 pb-16 pt-36">
        <h2 className="mb-6 font-serif text-2xl font-semibold text-ink">
          {cats.find((c) => c.id === shownCat)?.name}
        </h2>

        <section className="space-y-10">
          {visibleItems.map((it) => (
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
                </div>
                {!it.image_url && (
                  <span className="font-jakarta text-lg font-bold text-olive-700">
                    {money(it.price)}
                  </span>
                )}
              </div>
              <div className="border-b border-hairline/30" />
            </article>
          ))}
        </section>
      </main>

      <footer className="border-t border-hairline/30 px-6 py-5 text-center">
        <p className="font-serif text-sm text-ink-soft">
          {data.restaurant.name} · Dijital Menü
        </p>
        <p className="mt-1 text-xs text-ink-soft/70">
          Sipariş ve ödeme için masanızdaki QR kodu okutun.
        </p>
      </footer>
    </div>
  );
}
