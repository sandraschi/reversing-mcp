import path from "path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    host: "127.0.0.1",
    port: 10751,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:10750",
        changeOrigin: true,
      },
      "/health": {
        target: "http://127.0.0.1:10750",
        changeOrigin: true,
      },
      "/tools": {
        target: "http://127.0.0.1:10750",
        changeOrigin: true,
      },
      "/analyze": {
        target: "http://127.0.0.1:10750",
        changeOrigin: true,
      },
      "/ghidra": {
        target: "http://127.0.0.1:10750",
        changeOrigin: true,
      },
      "/llm": {
        target: "http://127.0.0.1:10750",
        changeOrigin: true,
      },
      "/skill": {
        target: "http://127.0.0.1:10750",
        changeOrigin: true,
      },
    },
  },
});
