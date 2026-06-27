import { fileURLToPath, URL } from "node:url";

import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig, type Plugin } from "vite";

// Müşteri uygulaması (ayrı port/domain): customer.html'i kök olarak sunar ve
// tüm SPA rotalarını (/r/.., /m/..) ona düşürür.
const proxyTarget = process.env.VITE_PROXY_TARGET ?? "http://localhost:8000";
const usePolling = process.env.VITE_USE_POLLING === "true";

function customerRoot(): Plugin {
  return {
    name: "customer-html-root",
    configureServer(server) {
      server.middlewares.use((req, _res, next) => {
        const url = req.url ?? "/";
        const isInternal =
          url.startsWith("/@") ||
          url.startsWith("/src") ||
          url.startsWith("/node_modules") ||
          url.startsWith("/api") ||
          url.includes(".");
        if (!isInternal) req.url = "/customer.html";
        next();
      });
    },
  };
}

export default defineConfig({
  plugins: [customerRoot(), react(), tailwindcss()],
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
      },
    },
  },
});
