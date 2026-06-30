import { useMutation } from "@tanstack/react-query";
import { type FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";

import { adminApi } from "@shared/api/admin";
import { ApiError } from "@shared/api/client";
import { useAdminStore } from "@shared/store/adminStore";
import { Button } from "@shared/ui/Button";
import { Card } from "@shared/ui/Card";
import { Input } from "@shared/ui/Input";

export function AdminLoginPage() {
  const navigate = useNavigate();
  const setAuth = useAdminStore((s) => s.setAuth);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const mutation = useMutation({
    mutationFn: () => adminApi.login(email, password),
    onSuccess: (auth) => {
      setAuth(auth);
      navigate("/admin", { replace: true });
    },
  });

  const errorMessage =
    mutation.error instanceof ApiError
      ? mutation.error.message
      : mutation.error
        ? "Bir hata oluştu, tekrar deneyin."
        : null;

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    mutation.mutate();
  };

  return (
    <div className="flex min-h-full items-center justify-center bg-slate-900 p-4">
      <Card className="w-full max-w-md p-8">
        <div className="mb-6 text-center">
          <h1 className="text-2xl font-bold text-brand-800">Kasa · Platform</h1>
          <p className="mt-1 text-sm text-slate-500">Yönetici paneli</p>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <Input
            label="E-posta"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="admin@kasa.app"
            required
            autoComplete="email"
          />
          <Input
            label="Parola"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            required
            autoComplete="current-password"
          />

          {errorMessage && (
            <div
              role="alert"
              className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700"
            >
              {errorMessage}
            </div>
          )}

          <Button type="submit" loading={mutation.isPending} className="w-full">
            Giriş Yap
          </Button>
        </form>
      </Card>
    </div>
  );
}
