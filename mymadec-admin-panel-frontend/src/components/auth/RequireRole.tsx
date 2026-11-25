import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../../store/auth";
import type { User } from "../../lib/types";
import { PageLoader } from "../ui/Spinner";
import { ForbiddenPage } from "../ui/ForbiddenPage";

interface RequireRoleProps {
  children: React.ReactNode;
  roles?: User["role"][];
}

/**
 * Route guard: shows a proper "Accès interdit" page instead of silently
 * redirecting to dashboard when a user navigates to a restricted route.
 * This way the user understands WHY they can't access the page.
 */
export function RequireRole({ children, roles }: RequireRoleProps) {
  const { user } = useAuth();
  const [hydrated, setHydrated] = useState(() => useAuth.persist.hasHydrated());

  useEffect(() => {
    if (hydrated) return;
    const unsub = useAuth.persist.onFinishHydration(() => setHydrated(true));
    if (useAuth.persist.hasHydrated()) setHydrated(true);
    return unsub;
  }, [hydrated]);

  if (!hydrated) return <PageLoader />;

  if (!user) return <Navigate to="/login" replace />;

  if (roles && !roles.includes(user.role)) {
    return <ForbiddenPage />;
  }

  return <>{children}</>;
}
