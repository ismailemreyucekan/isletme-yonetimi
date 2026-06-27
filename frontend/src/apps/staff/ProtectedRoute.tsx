import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";

import { useAuthStore } from "@shared/store/authStore";

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const accessToken = useAuthStore((s) => s.accessToken);
  const location = useLocation();

  if (!accessToken) {
    return <Navigate to="/staff/login" state={{ from: location }} replace />;
  }
  return <>{children}</>;
}
