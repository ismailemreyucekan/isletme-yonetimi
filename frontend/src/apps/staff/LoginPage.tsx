import { useMutation } from "@tanstack/react-query";
import { type FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";

import { authApi } from "@shared/api/auth";
import { ApiError } from "@shared/api/client";
import { useAuthStore } from "@shared/store/authStore";
import type { AuthResponse } from "@shared/types";
import { Button } from "@shared/ui/Button";
import { Card } from "@shared/ui/Card";
import { Input } from "@shared/ui/Input";

type Mode = "login" | "register";

export function LoginPage() {
  const navigate = useNavigate();
  const setAuth = useAuthStore((s) => s.setAuth);
  const [mode, setMode] = useState<Mode>("login");

  const [restaurantName, setRestaurantName] = useState("");
  const [ownerName, setOwnerName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const onSuccess = (auth: AuthResponse) => {
    setAuth(auth);
    navigate("/staff", { replace: true });
  };

  const mutation = useMutation({
    mutationFn: async () =>
      mode === "login"
        ? authApi.login({ email, password })
        : authApi.register({
            restaurant_name: restaurantName,
            owner_name: ownerName,
            email,
            password,
          }),
    onSuccess,
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
    <div className="flex min-h-full items-center justify-center bg-slate-100 p-4">
      <Card className="w-full max-w-md p-8">
        <div className="mb-6 text-center">
          <h1 className="text-2xl font-bold text-brand-800">Kasa</h1>
          <p className="mt-1 text-sm text-slate-500">Personel paneli</p>
        </div>

        <div className="mb-6 grid grid-cols-2 gap-1 rounded-lg bg-slate-100 p-1">
          {(["login", "register"] as const).map((m) => (
            <button
              key={m}
              type="button"
              onClick={() => {
                setMode(m);
                mutation.reset();
              }}
              className={[
                "rounded-md py-2 text-sm font-semibold transition-colors",
                mode === m
                  ? "bg-white text-brand-800 shadow-sm"
                  : "text-slate-500 hover:text-slate-700",
              ].join(" ")}
            >
              {m === "login" ? "Giriş Yap" : "İşletme Kaydı"}
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          {mode === "register" && (
            <>
              <Input
                label="İşletme adı"
                value={restaurantName}
                onChange={(e) => setRestaurantName(e.target.value)}
                placeholder="Kafe Lojik"
                required
                minLength={2}
              />
              <Input
                label="Ad soyad"
                value={ownerName}
                onChange={(e) => setOwnerName(e.target.value)}
                placeholder="Adınız"
                required
                minLength={2}
              />
            </>
          )}
          <Input
            label="E-posta"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="ornek@isletme.com"
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
            minLength={8}
            autoComplete={mode === "login" ? "current-password" : "new-password"}
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
            {mode === "login" ? "Giriş Yap" : "Kayıt Ol"}
          </Button>
        </form>
      </Card>
    </div>
  );
}
