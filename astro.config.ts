import { defineConfig } from "astro/config";
import icon from "astro-icon";
import expressiveCode from "astro-expressive-code";
import type { AstroExpressiveCodeOptions } from "astro-expressive-code";
import tailwind from "@astrojs/tailwind";
import mdx from "@astrojs/mdx";

const astroExpressiveCodeOptions: AstroExpressiveCodeOptions = {
  themes: ["monokai"],
  styleOverrides: {
    codeFontFamily: "'Jetbrains Mono', ui-monospace, Consolas, monospace",
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
    mdx(),
  ],
});
