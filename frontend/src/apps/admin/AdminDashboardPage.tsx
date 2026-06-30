import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { adminApi } from "@shared/api/admin";
import { useAdminStore } from "@shared/store/adminStore";
import type { AdminRestaurant, FeatureCatalogItem } from "@shared/types";
import { Button } from "@shared/ui/Button";
import { Card } from "@shared/ui/Card";

export function AdminDashboardPage() {
  const navigate = useNavigate();
  const admin = useAdminStore((s) => s.admin);
  const logout = useAdminStore((s) => s.logout);
  const queryClient = useQueryClient();

  const featuresQuery = useQuery({
    queryKey: ["admin", "features"],
    queryFn: adminApi.features,
    staleTime: 5 * 60_000,
  });

  const restaurantsQuery = useQuery({
    queryKey: ["admin", "restaurants"],
    queryFn: adminApi.restaurants,
  });

  const toggleMutation = useMutation({
    mutationFn: ({
      restaurantId,
      features,
    }: {
      restaurantId: string;
      features: Record<string, boolean | null>;
    }) => adminApi.updateFeatures(restaurantId, features),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "restaurants"] });
    },
  });

  const handleLogout = () => {
    logout();
    navigate("/admin/login", { replace: true });
  };

  return (
    <div className="min-h-full bg-slate-100">
      <header className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-4">
        <div>
          <h1 className="text-lg font-bold text-brand-800">Kasa · Platform Yönetimi</h1>
          <p className="text-xs text-slate-500">{admin?.email}</p>
        </div>
        <Button variant="secondary" onClick={handleLogout}>
          Çıkış
        </Button>
      </header>

      <main className="mx-auto max-w-5xl space-y-4 p-6">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-600">
            İşletmeler {restaurantsQuery.data ? `(${restaurantsQuery.data.length})` : ""}
          </h2>
          {toggleMutation.isError && (
            <span className="text-xs text-red-600">
              Güncelleme başarısız, tekrar deneyin.
            </span>
          )}
        </div>

        {restaurantsQuery.isLoading && (
          <p className="text-sm text-slate-500">Yükleniyor…</p>
        )}
        {restaurantsQuery.isError && (
          <p className="text-sm text-red-600">İşletmeler yüklenemedi.</p>
        )}

        {restaurantsQuery.data?.map((r) => (
          <RestaurantRow
            key={r.id}
            restaurant={r}
            catalog={featuresQuery.data ?? []}
            busy={toggleMutation.isPending}
            onToggle={(key, value) =>
              toggleMutation.mutate({
                restaurantId: r.id,
                features: { [key]: value },
              })
            }
          />
        ))}
      </main>
    </div>
  );
}

function RestaurantRow({
  restaurant,
  catalog,
  busy,
  onToggle,
}: {
  restaurant: AdminRestaurant;
  catalog: FeatureCatalogItem[];
  busy: boolean;
  onToggle: (key: string, value: boolean | null) => void;
}) {
  return (
    <Card className="p-5">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 className="font-semibold text-slate-800">{restaurant.name}</h3>
          <p className="text-xs text-slate-500">
            /{restaurant.slug} · {restaurant.owner_email ?? "—"} ·{" "}
            {restaurant.user_count} kullanıcı
          </p>
        </div>
        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
          Plan: {restaurant.plan}
        </span>
      </div>

      <div className="grid gap-2 sm:grid-cols-2">
        {catalog.map((feat) => {
          const enabled = restaurant.features[feat.key] ?? false;
          return (
            <div
              key={feat.key}
              className="flex items-center justify-between gap-3 rounded-lg border border-slate-200 px-3 py-2"
            >
              <div className="min-w-0">
                <p className="text-sm font-medium text-slate-800">{feat.label}</p>
                <p className="truncate text-xs text-slate-500">{feat.description}</p>
              </div>
              <button
                type="button"
                disabled={busy}
                onClick={() => onToggle(feat.key, !enabled)}
                aria-pressed={enabled}
                className={[
                  "relative h-6 w-11 shrink-0 rounded-full transition-colors disabled:opacity-50",
                  enabled ? "bg-brand-600" : "bg-slate-300",
                ].join(" ")}
              >
                <span
                  className={[
                    "absolute top-0.5 size-5 rounded-full bg-white shadow transition-all",
                    enabled ? "left-[22px]" : "left-0.5",
                  ].join(" ")}
                />
              </button>
            </div>
          );
        })}
      </div>
    </Card>
  );
}
