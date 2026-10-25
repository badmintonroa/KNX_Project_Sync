// Bundle generate.ts together with the knx2home sources it imports.
// KNX2HOME_DIR points to a knx2home checkout with installed node_modules.
import { build } from "esbuild";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const knx2home = path.resolve(process.env.KNX2HOME_DIR ?? path.join(here, "../../../knx2home"));

await build({
  entryPoints: [path.join(here, "generate.ts")],
  outfile: path.join(here, "dist/generate.cjs"),
  bundle: true,
  platform: "node",
  format: "cjs",
  target: "node20",
  alias: { "@": path.join(knx2home, "src") },
  nodePaths: [path.join(knx2home, "node_modules")],
  define: { "process.env.KNX2HOME_DIR_BUILT": JSON.stringify(knx2home) },
  logLevel: "warning",
});
