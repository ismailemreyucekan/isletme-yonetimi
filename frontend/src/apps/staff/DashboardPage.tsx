import { useQuery } from "@tanstack/react-query";

import { authApi } from "@shared/api/auth";
import { Card } from "@shared/ui/Card";

const ROLE_LABELS: Record<string, string> = {
  owner: "Sahip",
  manager: "Yönetici",
  cashier: "Kasiyer",
  waiter: "Garson",
};

export function DashboardPage() {
  const meQuery = useQuery({ queryKey: ["me"], queryFn: authApi.me });
  const restaurantQuery = useQuery({
    queryKey: ["my-restaurant"],
    queryFn: authApi.myRestaurant,
  });

  return (
    <div className="mx-auto max-w-5xl p-6">
      <header className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">
          {restaurantQuery.data?.name ?? "Yükleniyor…"}
        </h1>
        <p className="text-sm text-slate-500">Personel Paneli</p>
      </header>

      <div className="grid gap-4 sm:grid-cols-2">
        <Card className="p-6">
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-400">
            Oturum Açan Kullanıcı
          </h2>
          {meQuery.isLoading ? (
            <p className="text-slate-500">Yükleniyor…</p>
          ) : meQuery.data ? (
            <dl className="space-y-2 text-sm">
              <Row label="Ad" value={meQuery.data.name} />
              <Row label="E-posta" value={meQuery.data.email} />
              <Row
                label="Rol"
                value={ROLE_LABELS[meQuery.data.role] ?? meQuery.data.role}
              />
            </dl>
          ) : (
            <p className="text-red-600">Kullanıcı bilgisi alınamadı.</p>
          )}
        </Card>

        <Card className="p-6">
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-400">
            İşletme
          </h2>
          {restaurantQuery.data ? (
            <dl className="space-y-2 text-sm">
              <Row label="Ad" value={restaurantQuery.data.name} />
              <Row label="Slug" value={restaurantQuery.data.slug} />
              <Row label="Plan" value={restaurantQuery.data.plan} />
            </dl>
          ) : (
            <p className="text-slate-500">Yükleniyor…</p>
          )}
        </Card>
      </div>

      <Card className="mt-4 border-dashed bg-slate-50 p-6">
        <h2 className="mb-1 font-semibold text-slate-700">Sonraki adım</h2>
        <p className="text-sm text-slate-500">
          Faz 2 — POS: masa listesi, sipariş alma, hesap kapatma.
        </p>
      </Card>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-4">
      <dt className="text-slate-400">{label}</dt>
      <dd className="font-medium text-slate-800">{value}</dd>
    </div>
  );
}
