import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

const isStorybook = Boolean(process.env.STORYBOOK);

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      disable: isStorybook,
      filename: "v10-sw.js",
      registerType: "autoUpdate",
      injectRegister: "auto",
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
        navigateFallback: "/index.html",
        additionalManifestEntries: [{ url: "/index.html", revision: "v10-shell" }],
        cleanupOutdatedCaches: true,
        runtimeCaching: [
          {
            urlPattern: ({ request, url }) =>
              request.destination === "document" && url.pathname.startsWith("/v8/"),
            handler: "NetworkFirst",
            options: {
              cacheName: "citynexus-pages",
              networkTimeoutSeconds: 3,
              cacheableResponse: { statuses: [0, 200] },
            },
          },
          {
            urlPattern: ({ request, url }) =>
              !url.pathname.startsWith("/api/") &&
              ["script", "style", "worker", "image", "font"].includes(
                request.destination,
              ),
            handler: "CacheFirst",
            options: {
              cacheName: "citynexus-static",
              cacheableResponse: { statuses: [0, 200] },
            },
          },
        ],
      },
      devOptions: {
        enabled: true,
        navigateFallbackAllowlist: [/^\/(?:v8|index)/],
      },
    }),
  ],
  server: {
    proxy: {
      "/api/v1": {
        target: "http://127.0.0.1:8000",
        changeOrigin: false,
      },
    },
  },
});
