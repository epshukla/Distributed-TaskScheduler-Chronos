import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

const API_TARGET = process.env.VITE_API_TARGET || "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: API_TARGET,
        changeOrigin: true,
      },
      "/internal": {
        target: API_TARGET,
        changeOrigin: true,
      },
      "/ws/events": {
        target: API_TARGET,
        changeOrigin: true,
        ws: true,
      },
      "/health": {
        target: API_TARGET,
        changeOrigin: true,
      },
      "/ready": {
        target: API_TARGET,
        changeOrigin: true,
      },
    },
  },
});
