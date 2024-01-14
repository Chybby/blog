import type { Config } from "tailwindcss";

export default {
  content: ["./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}"],
  darkMode: "class",
  theme: {
    fontFamily: {
      sans: ["Outfit", "sans-serif"],
      serif: ["Roboto Slab", "serif"],
      mono: ["Jetbrains Mono", "mono"],
    },
  },
  plugins: [require("@tailwindcss/typography")],
} satisfies Config;
