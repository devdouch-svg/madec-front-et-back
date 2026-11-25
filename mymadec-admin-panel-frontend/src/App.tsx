import { lazy, Suspense, useState, type ReactNode } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "react-hot-toast";

import { AppLayout }           from "./components/layout/AppLayout";
import { RequireRole }         from "./components/auth/RequireRole";
import { PageLoader }          from "./components/ui/Spinner";
const LoginPage           = lazy(() => import("./pages/LoginPage").then((m) => ({ default: m.LoginPage })));
const ForgotPasswordPage  = lazy(() => import("./pages/ForgotPasswordPage").then((m) => ({ default: m.ForgotPasswordPage })));
const ResetPasswordPage   = lazy(() => import("./pages/ResetPasswordPage").then((m) => ({ default: m.ResetPasswordPage })));
const DashboardPage       = lazy(() => import("./pages/DashboardPage").then((m) => ({ default: m.DashboardPage })));
const ProductsPage        = lazy(() => import("./pages/ProductsPage").then((m) => ({ default: m.ProductsPage })));
const OrdersPage          = lazy(() => import("./pages/OrdersPage").then((m) => ({ default: m.OrdersPage })));
const UsersPage           = lazy(() => import("./pages/UsersPage").then((m) => ({ default: m.UsersPage })));
const CatalogPage         = lazy(() => import("./pages/CatalogPage").then((m) => ({ default: m.CatalogPage })));
const CatalogSortPage     = lazy(() => import("./pages/CatalogSortPage").then((m) => ({ default: m.CatalogSortPage })));
const NotificationsPage   = lazy(() => import("./pages/NotificationsPage").then((m) => ({ default: m.NotificationsPage })));
const ProfilePage         = lazy(() => import("./pages/ProfilePage").then((m) => ({ default: m.ProfilePage })));
const AnnuairePage        = lazy(() => import("./pages/AnnuairePage").then((m) => ({ default: m.AnnuairePage })));
const BannersPage         = lazy(() => import("./pages/BannersPage").then((m) => ({ default: m.BannersPage })));
const PaymentMethodsPage  = lazy(() => import("./pages/PaymentMethodsPage").then((m) => ({ default: m.PaymentMethodsPage })));
const SyncPage            = lazy(() => import("./pages/SyncPage").then((m) => ({ default: m.SyncPage })));
const PromptinosPage      = lazy(() => import("./pages/PromptinosPage").then((m) => ({ default: m.PromptinosPage })));

function PageSuspense({ children }: { children: ReactNode }) {
  return <Suspense fallback={<PageLoader />}>{children}</Suspense>;
}

export default function App() {
  const [qc] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            retry: 1,
            staleTime: 30_000,
            gcTime: 5 * 60_000,
            refetchOnWindowFocus: false,
          },
          mutations: {
            retry: 0,
          },
        },
      }),
  );

  return (
    <QueryClientProvider client={qc}>
      <BrowserRouter basename={import.meta.env.BASE_URL.replace(/\/$/, "")}>
        <Routes>
          <Route path="/login" element={<PageSuspense><LoginPage /></PageSuspense>} />
          <Route path="/forgot-password" element={<PageSuspense><ForgotPasswordPage /></PageSuspense>} />
          <Route path="/reset-password" element={<PageSuspense><ResetPasswordPage /></PageSuspense>} />

          <Route element={<AppLayout />}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<PageSuspense><DashboardPage /></PageSuspense>} />
            <Route path="/products" element={<PageSuspense><ProductsPage /></PageSuspense>} />
            <Route path="/promptinos" element={<PageSuspense><PromptinosPage /></PageSuspense>} />
            <Route path="/orders" element={<PageSuspense><OrdersPage /></PageSuspense>} />
            <Route
              path="/annuaire"
              element={
                <RequireRole roles={["admin"]}>
                  <PageSuspense><AnnuairePage /></PageSuspense>
                </RequireRole>
              }
            />
            <Route path="/profile" element={<PageSuspense><ProfilePage /></PageSuspense>} />
            <Route path="/notifications" element={<PageSuspense><NotificationsPage /></PageSuspense>} />

            <Route
              path="/users"
              element={
                <RequireRole roles={["admin", "gestionnaire"]}>
                  <PageSuspense><UsersPage /></PageSuspense>
                </RequireRole>
              }
            />
            <Route
              path="/catalog/order"
              element={
                <RequireRole roles={["admin", "gestionnaire"]}>
                  <PageSuspense><CatalogSortPage /></PageSuspense>
                </RequireRole>
              }
            />
            <Route
              path="/catalog"
              element={
                <RequireRole roles={["admin", "gestionnaire"]}>
                  <PageSuspense><CatalogPage /></PageSuspense>
                </RequireRole>
              }
            />
            <Route
              path="/banners"
              element={
                <RequireRole roles={["admin"]}>
                  <PageSuspense><BannersPage /></PageSuspense>
                </RequireRole>
              }
            />
            <Route
              path="/payment-methods"
              element={
                <RequireRole roles={["acheteur", "admin"]}>
                  <PageSuspense><PaymentMethodsPage /></PageSuspense>
                </RequireRole>
              }
            />
            <Route
              path="/sync"
              element={
                <RequireRole roles={["admin"]}>
                  <PageSuspense><SyncPage /></PageSuspense>
                </RequireRole>
              }
            />
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>

      <Toaster
        position="top-center"
        gutter={12}
        containerStyle={{ top: 24, zIndex: 9999 }}
        toastOptions={{
          duration: 4000,
          className: "madec-toast",
          style: {
            fontSize: "15px",
            fontWeight: 500,
            lineHeight: "1.45",
            maxWidth: "440px",
            minWidth: "min(360px, calc(100vw - 32px))",
            padding: "14px 18px",
            borderRadius: "0.4rem",
            border: "1px solid #e9e9ef",
            color: "#313533",
            background: "#fff",
            boxShadow: "rgba(116, 120, 141, 0.18) 0px 10px 28px -8px",
          },
          success: {
            className: "madec-toast madec-toast--success",
            iconTheme: { primary: "#2ab57d", secondary: "#fff" },
            style: {
              background: "#d4f0e5",
              border: "1px solid #2ab57d",
              color: "#1e7a55",
            },
          },
          error: {
            className: "madec-toast madec-toast--error",
            iconTheme: { primary: "#fd625e", secondary: "#fff" },
            style: {
              background: "#ffe0df",
              border: "1px solid #fd625e",
              color: "#c0392b",
            },
          },
        }}
      />
    </QueryClientProvider>
  );
}
