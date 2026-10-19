import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

// BASE_PATH sets the public path for static hosting, e.g. "/memory-xray/" for
// https://<user>.github.io/memory-xray/ . Defaults to "./" (relative), which works from
// any folder, including a local file server.
export default defineConfig({
  base: process.env.BASE_PATH ?? "./",
  plugins: [react()],
  build: {
    outDir: "dist",
    sourcemap: false,
    chunkSizeWarningLimit: 900,
  },
  test: {
    include: ["tests/unit/**/*.test.ts"],
  },
});
