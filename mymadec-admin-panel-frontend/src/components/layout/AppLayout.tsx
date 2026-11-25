import { useEffect, useState } from "react";
import { Outlet, Navigate } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";
import { SidebarProvider } from "./SidebarContext";
import { ErrorBoundary } from "../ErrorBoundary";
import { useAuth } from "../../store/auth";
import { clearSession } from "../../lib/session";
import { LOGIN_URL } from "../../lib/config";
import { PageLoader } from "../ui/Spinner";

export function AppLayout() {
  const { user, fetchMe, accessToken } = useAuth();

  // Initialise synchronously — localStorage hydration in Zustand is synchronous,
  // so hasHydrated() is already true on the first render in most cases.
  // The useState + useEffect pattern covers the rare async-storage edge case.
  const [hydrated, setHydrated] = useState(() => useAuth.persist.hasHydrated());

  useEffect(() => {
    if (hydrated) return;
    const unsub = useAuth.persist.onFinishHydration(() => setHydrated(true));
    // In case it already hydrated between the useState initialiser and this effect
    if (useAuth.persist.hasHydrated()) setHydrated(true);
    return unsub;
  }, [hydrated]);

  useEffect(() => {
    if (!hydrated || !accessToken) return;
    fetchMe().catch(() => {
      clearSession();
      useAuth.setState({ user: null, accessToken: null, refreshToken: null });
      window.location.replace(LOGIN_URL);
    });
  }, [hydrated, accessToken, fetchMe]);

  if (!hydrated) return <PageLoader />;

  if (!user || !accessToken) return <Navigate to="/login" replace />;

  if (user.role === "service") return <Navigate to="/login" replace />;

  return (
    <SidebarProvider>
      <div className="flex h-screen bg-white">
        <Sidebar />
        <div className="flex min-w-0 flex-1 flex-col">
          <TopBar />
          <main className="flex-1 overflow-y-auto bg-white">
            <ErrorBoundary>
              <Outlet />
            </ErrorBoundary>
          </main>
        </div>
      </div>
    </SidebarProvider>
  );
}
