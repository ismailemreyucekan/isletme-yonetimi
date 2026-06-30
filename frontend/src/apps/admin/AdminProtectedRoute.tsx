import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";

import { useAdminStore } from "@shared/store/adminStore";

export function AdminProtectedRoute({ children }: { children: ReactNode }) {
  const accessToken = useAdminStore((s) => s.accessToken);
  const location = useLocation();

  if (!accessToken) {
    return <Navigate to="/admin/login" state={{ from: location }} replace />;
  }
  return <>{children}</>;
}
