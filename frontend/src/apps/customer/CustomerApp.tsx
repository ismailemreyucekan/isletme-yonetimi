import { Navigate, Route, Routes } from "react-router-dom";

import { CustomerMenuPage } from "@/apps/customer/CustomerMenuPage";
import { CustomerPage, CustomerPaymentPage } from "@/apps/customer/CustomerPage";

// Müşteri uygulaması (ayrı port/domain). Her masa QR'ı sabittir; okutunca
// doğrudan o masanın menü+sipariş ekranına girer.
const DEMO_SLUG = import.meta.env.VITE_DEMO_SLUG ?? "";

export function CustomerApp() {
  return (
    <Routes>
      {/* Masa QR'ı: doğrudan menü + sipariş */}
      <Route path="/r/:slug/t/:token" element={<CustomerPage />} />
      {/* Ödeme sayfası (sağ üst "Ödeme" butonu yönlendirir) */}
      <Route path="/r/:slug/t/:token/odeme" element={<CustomerPaymentPage />} />

      {/* Sadece menü görüntüleme (masasız, QR olmadan) */}
      <Route path="/m/:slug" element={<CustomerMenuPage />} />

      {/* Kök: QR olmadan açıldıysa işletmenin menüsünü göster */}
      <Route
        path="/"
        element={DEMO_SLUG ? <Navigate to={`/m/${DEMO_SLUG}`} replace /> : <Landing />}
      />

      <Route path="*" element={<Landing />} />
    </Routes>
  );
}

function Landing() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-3 bg-cream p-8 text-center font-jakarta">
      <span className="material-symbols-outlined text-5xl text-olive-600">qr_code_scanner</span>
      <h1 className="font-serif text-2xl font-bold text-olive-700">QR Menü & Ödeme</h1>
      <p className="max-w-xs text-sm text-ink-soft">
        Menüyü görmek, sipariş vermek ve ödeme yapmak için masanızdaki QR kodu
        telefonunuzla okutun.
      </p>
    </div>
  );
}
