// Screenshots of the panel with the test data of the smoke test, for the README:
import { readFileSync } from "node:fs";
import http from "node:http";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { chromium } from "playwright";

const here = path.dirname(fileURLToPath(import.meta.url));
const out = path.join(here, "../../docs/images");
const bundle = readFileSync(path.join(here, "../../custom_components/knx_project_sync/frontend/knx-project-sync-panel.js"));
const plan = readFileSync(path.join(here, "plan.json"));

const page = (lang, dark, narrow) => `<!doctype html><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<body style="margin:0;background:${dark ? "#111" : "#fafafa"};font-family:Roboto,system-ui,sans-serif">
<script type="module">
import "/panel.js";
const plan = await (await fetch("/plan.json")).json();
${dark ? `document.documentElement.style.cssText = "--primary-background-color:#111;--card-background-color:#1c1c1c;--primary-text-color:#e1e1e1;--secondary-text-color:#9b9b9b;--divider-color:rgba(225,225,225,.12)";` : ""}
const el = document.createElement("knx-project-sync-panel");
el.hass = {
  language: "${lang}",
  async callWS(msg) { return msg.type.endsWith("/plan") ? plan : {}; },
  async fetchWithAuth() { return new Response("{}"); },
};
el.narrow = ${narrow};
document.body.append(el);
</script>`;

const server = http
  .createServer((req, res) => {
    const url = new URL(req.url, "http://x");
    const q = url.searchParams;
    if (url.pathname === "/panel.js") res.writeHead(200, { "content-type": "text/javascript" }).end(bundle);
    else if (url.pathname === "/plan.json") res.writeHead(200, { "content-type": "application/json" }).end(plan);
    else res.writeHead(200, { "content-type": "text/html" }).end(page(q.get("lang"), q.has("dark"), q.has("narrow")));
  })
  .listen(0);
const base = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch(process.env.PW_CHROMIUM ? { executablePath: process.env.PW_CHROMIUM } : {});
try {
  for (const [file, query, width, height] of [
    ["panel-en.png", "?lang=en", 1200, 1000],
    ["panel-de.png", "?lang=de", 1200, 1000],
    ["panel-dark.png", "?lang=en&dark", 1200, 1000],
  ]) {
    const tab = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: 2 });
    await tab.goto(`${base}/${query}`);
    await tab.waitForSelector("knx-project-sync-panel >> .row");
    await tab.waitForTimeout(300);
    await tab.screenshot({ path: path.join(out, file) });
    await tab.close();
  }
} finally {
  await browser.close();
  server.close();
}
