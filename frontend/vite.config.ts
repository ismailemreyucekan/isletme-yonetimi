import { fileURLToPath, URL } from "node:url";

import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Dev'de /api isteklerini backend'e yönlendir (CORS'suz geliştirme).
const proxyTarget = process.env.VITE_PROXY_TARGET ?? "http://localhost:8000";

// Docker bind-mount'ta (özellikle Windows) HMR için dosya izlemeyi polling'e al.
const usePolling = process.env.VITE_USE_POLLING === "true";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
      "@shared": fileURLToPath(new URL("./src/shared", import.meta.url)),
    },
  },
  server: {
    host: true,
    port: 5173,
    watch: usePolling ? { usePolling: true } : undefined,
    proxy: {
      "/api": {
        target: proxyTarget,
        changeOrigin: true,
        ws: true, // KDS WebSocket'i (/api/v1/kds/ws) de proxy'le
      },
    },
  },
});
