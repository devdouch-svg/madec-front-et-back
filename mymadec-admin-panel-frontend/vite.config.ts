import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const proxyTarget = env.VITE_DEV_PROXY_TARGET || "http://127.0.0.1:8000";

  const proxy = {
    "/api": { target: proxyTarget, changeOrigin: true, secure: false },
    "/uploads": { target: proxyTarget, changeOrigin: true, secure: false },
  };

  return {
    // v2 is now the main app, served at the root /
    base: "/",
    plugins: [react()],
    server: { host: true, port: 5173, proxy },
    preview: { port: 4173, proxy },
  };
});
