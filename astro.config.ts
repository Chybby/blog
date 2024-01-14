import { defineConfig } from "astro/config";
import icon from "astro-icon";
import expressiveCode from "astro-expressive-code";
import type { AstroExpressiveCodeOptions } from "astro-expressive-code";
import tailwind from "@astrojs/tailwind";

const astroExpressiveCodeOptions: AstroExpressiveCodeOptions = {
  themes: ["monokai"],
  styleOverrides: {
    codeFontFamily: ["Jetbrains Mono", "monospace"],
  },
};

// https://astro.build/config
export default defineConfig({
  site: "https://blog.chybby.com",
  integrations: [
    icon({
      include: {
        mdi: ["*"],
        cib: ["itch-io"],
      },
    }),
    expressiveCode(astroExpressiveCodeOptions),
    tailwind(),
  ],
});
