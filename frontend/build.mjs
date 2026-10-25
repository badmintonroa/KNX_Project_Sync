// Bundles the panel into one ES module inside the integration (served by HA).
import { build } from "esbuild";

await build({
  entryPoints: ["src/panel.ts"],
  outfile: "../custom_components/knx_project_sync/frontend/knx-project-sync-panel.js",
  bundle: true,
  format: "esm",
  target: "es2021",
  minify: true,
  legalComments: "eof",
  logLevel: "info",
});
