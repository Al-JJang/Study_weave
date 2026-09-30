import { fileURLToPath } from "node:url";
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

const srcDir = fileURLToPath(new URL("./src", import.meta.url));

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": srcDir,
    },
  },
  server: {
    host: "0.0.0.0",
    port: 43180,
    proxy: {
      "/api": "http://127.0.0.1:43181",
    },
  },
  preview: {
    host: "0.0.0.0",
    port: 43180,
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./src/test/setup.ts",
  },
});
