import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

const isStorybook = Boolean(process.env.STORYBOOK);
const runtimeCacheVersion = "m3-a4-v1";
const documentNetworkTimeoutSeconds = 8;

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      disable: isStorybook,
      filename: "v10-sw.js",
      registerType: "autoUpdate",
      // main.tsx owns registration. Development never registers a production
      // worker; production always registers this generated worker.
      injectRegister: false,
      includeAssets: ["favicon.svg"],
      manifest: {
        name: "CityNexus Live Journey",
        short_name: "CityNexus",
        description: "Read-only offline journey execution companion",
        theme_color: "#092e34",
        background_color: "#f4f6f2",
        display: "standalone",
        start_url: "/v8/live",
        icons: [{ src: "/favicon.svg", sizes: "any", type: "image/svg+xml" }],
      },
      workbox: {
        maximumFileSizeToCacheInBytes: 3 * 1024 * 1024,
        navigateFallback: "/index.html",
        // A navigation fallback is only for documents. API and asset URLs must
        // fail as themselves rather than being replaced by the SPA HTML shell.
        navigateFallbackDenylist: [
          /^\/api\//,
          /\/assets\//,
          /\.(?:js|mjs|css|map|json|wasm|ico|svg|png|jpe?g|gif|webp|avif|woff2?|ttf|otf|webmanifest)$/i,
        ],
        cleanupOutdatedCaches: true,
        clientsClaim: true,
        skipWaiting: true,
        runtimeCaching: [
          {
            urlPattern: ({ request, url }) =>
              request.destination === "document" && url.pathname.startsWith("/v8/"),
            handler: "NetworkFirst",
            options: {
              cacheName: `citynexus-pages-${runtimeCacheVersion}`,
              // The previous 3s budget produced false stale-shell fallbacks on
              // real mobile/tunnel use. 8s is the M3-A4 candidate: CI must prove
              // that a 4s delayed document still returns the fresh network shell
              // while a >8s delay may use only a same-version cached document.
              networkTimeoutSeconds: documentNetworkTimeoutSeconds,
              cacheableResponse: { statuses: [200] },
              expiration: {
                maxEntries: 12,
                maxAgeSeconds: 24 * 60 * 60,
                purgeOnQuotaError: true,
              },
            },
          },
          {
            urlPattern: ({ request, url }) =>
              !url.pathname.startsWith("/api/") &&
              ["script", "style", "image", "font"].includes(request.destination),
            handler: "StaleWhileRevalidate",
            options: {
              cacheName: `citynexus-static-${runtimeCacheVersion}`,
              // Never persist opaque/status-0 executable responses. Vite's
              // script/style filenames are content-hashed; SWR therefore keeps
              // current assets responsive without pinning an old module graph.
              cacheableResponse: { statuses: [200] },
              expiration: {
                maxEntries: 96,
                maxAgeSeconds: 7 * 24 * 60 * 60,
                purgeOnQuotaError: true,
              },
            },
          },
        ],
      },
      devOptions: {
        enabled: false,
        navigateFallbackAllowlist: [/^\/(?:v8|index)/],
      },
    }),
  ],
  server: {
    proxy: {
      "/api/v1": {
        target: `http://127.0.0.1:${Number(process.env.CITYNEXUS_BACKEND_PORT ?? 8000)}`,
        changeOrigin: false,
      },
    },
  },
});
