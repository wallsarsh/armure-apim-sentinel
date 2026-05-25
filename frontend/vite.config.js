import { defineConfig } from "vite"
import vue from "@vitejs/plugin-vue"

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 8080,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
  optimizeDeps: {
    include: ["echarts", "vue-echarts", "lucide-vue-next"],
  },
  base: "/assets/armure_apim_sentinel/frontend/",
  build: {
    outDir: "../armure_apim_sentinel/public/frontend",
    assetsDir: "",
    emptyOutDir: true,
    sourcemap: true,
  },
})
