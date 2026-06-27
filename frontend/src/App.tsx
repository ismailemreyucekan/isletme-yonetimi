import { Navigate, Route, Routes } from "react-router-dom";

import { CustomerPage } from "@/apps/customer/CustomerPage";
import { KdsPage } from "@/apps/kds/KdsPage";
import { CouponsPage } from "@/apps/staff/CouponsPage";
import { DashboardPage } from "@/apps/staff/DashboardPage";
import { LoginPage } from "@/apps/staff/LoginPage";
import { MenuPage } from "@/apps/staff/MenuPage";
import { PosOrderPage } from "@/apps/staff/PosOrderPage";
import { ProtectedRoute } from "@/apps/staff/ProtectedRoute";
import { StaffLayout } from "@/apps/staff/StaffLayout";
import { TablesPage } from "@/apps/staff/TablesPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/staff" replace />} />

      {/* Personel paneli */}
      <Route path="/staff/login" element={<LoginPage />} />
      <Route
        path="/staff"
        element={
          <ProtectedRoute>
            <StaffLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="tables" element={<TablesPage />} />
        <Route path="menu" element={<MenuPage />} />
        <Route path="coupons" element={<CouponsPage />} />
      </Route>

      {/* POS sipariş ekranı (layout dışında, tam ekran) */}
      <Route
        path="/staff/pos/:tableId/:orderId"
        element={
          <ProtectedRoute>
            <PosOrderPage />
          </ProtectedRoute>
        }
      />

      {/* Mutfak ekranı */}
      <Route
        path="/kds"
        element={
          <ProtectedRoute>
            <KdsPage />
          </ProtectedRoute>
        }
      />

      {/* Müşteri QR ödeme (anonim) */}
      <Route path="/r/:slug/t/:token" element={<CustomerPage />} />

      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}

function NotFound() {
  return (
    <div className="flex min-h-full flex-col items-center justify-center gap-2 p-6 text-center">
      <h1 className="text-3xl font-bold text-slate-800">404</h1>
      <p className="text-slate-500">Sayfa bulunamadı.</p>
    </div>
  );
}
