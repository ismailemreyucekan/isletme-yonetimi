import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { type FormEvent, useState } from "react";

import { ApiError } from "@shared/api/client";
import { couponsApi } from "@shared/api/coupons";
import { Button } from "@shared/ui/Button";
import { Card } from "@shared/ui/Card";
import { Input } from "@shared/ui/Input";

export function CouponsPage() {
  const qc = useQueryClient();
  const { data: coupons = [], isLoading } = useQuery({
    queryKey: ["coupons"],
    queryFn: couponsApi.list,
  });

  const [code, setCode] = useState("");
  const [mode, setMode] = useState<"percent" | "amount">("percent");
  const [value, setValue] = useState("");

  const invalidate = () => qc.invalidateQueries({ queryKey: ["coupons"] });

  const create = useMutation({
    mutationFn: () => couponsApi.create(code.trim(), mode, Number(value) || 0),
    onSuccess: () => {
      invalidate();
      setCode("");
      setValue("");
    },
  });
  const remove = useMutation({
    mutationFn: (id: string) => couponsApi.remove(id),
    onSuccess: invalidate,
  });

  const errorMsg =
    create.error instanceof ApiError ? create.error.message : create.error ? "Hata" : null;

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    create.mutate();
  };

  return (
    <div className="mx-auto max-w-3xl p-6">
      <h1 className="mb-1 text-2xl font-bold text-slate-900">Kuponlar</h1>
      <p className="mb-6 text-sm text-slate-500">
        Kasada uygulanacak indirim kuponları. POS adisyonunda "İndirim → Kupon" ile kullanılır.
      </p>

      <Card className="mb-6 p-5">
        <h2 className="mb-3 font-semibold text-slate-800">Yeni Kupon</h2>
        <form onSubmit={onSubmit} className="flex flex-wrap items-end gap-3">
          <div className="min-w-40 flex-1">
            <Input
              label="Kod"
              value={code}
              onChange={(e) => setCode(e.target.value.toUpperCase())}
              placeholder="ORN. INDIRIM10"
              required
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Tür</label>
            <div className="grid grid-cols-2 gap-1 rounded-lg bg-slate-100 p-1">
              {(
                [
                  ["percent", "Yüzde %"],
                  ["amount", "Tutar ₺"],
                ] as const
              ).map(([m, label]) => (
                <button
                  key={m}
                  type="button"
                  onClick={() => setMode(m)}
                  className={[
                    "rounded-md px-3 py-2 text-sm font-medium",
                    mode === m ? "bg-white text-brand-700 shadow-sm" : "text-slate-500",
                  ].join(" ")}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
          <div className="w-28">
            <Input
              label="Değer"
              type="number"
              min={0}
              value={value}
              onChange={(e) => setValue(e.target.value)}
              placeholder={mode === "percent" ? "10" : "50"}
              required
            />
          </div>
          <Button type="submit" loading={create.isPending} disabled={!code || !value}>
            Ekle
          </Button>
        </form>
        {errorMsg && <p className="mt-2 text-sm text-red-600">{errorMsg}</p>}
      </Card>

      <Card className="divide-y divide-slate-100">
        {isLoading ? (
          <p className="p-5 text-slate-500">Yükleniyor…</p>
        ) : coupons.length === 0 ? (
          <p className="p-5 text-center text-slate-400">Henüz kupon yok.</p>
        ) : (
          coupons.map((c) => (
            <div key={c.id} className="flex items-center justify-between p-4">
              <div>
                <span className="font-mono font-semibold text-slate-800">{c.code}</span>
                <span className="ml-3 text-sm text-slate-500">
                  {c.mode === "percent" ? `%${Number(c.value)}` : `₺${Number(c.value)}`} indirim
                </span>
                {!c.is_active && (
                  <span className="ml-2 rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-500">
                    pasif
                  </span>
                )}
              </div>
              <button
                onClick={() => remove.mutate(c.id)}
                className="text-sm text-red-500 hover:underline"
              >
                Sil
              </button>
            </div>
          ))
        )}
      </Card>
    </div>
  );
}
