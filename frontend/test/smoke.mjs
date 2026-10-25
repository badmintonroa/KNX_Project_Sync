// Renders the built panel with a fake `hass` in Chromium (light, dark, phone width)
// and checks that choices end up in the selection sent to the backend.
import { readFileSync } from "node:fs";
import http from "node:http";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { chromium } from "playwright";

const here = path.dirname(fileURLToPath(import.meta.url));
const bundle = readFileSync(path.join(here, "../../custom_components/knx_project_sync/frontend/knx-project-sync-panel.js"));
const plan = readFileSync(path.join(here, "plan.json"));

const page = (dark, narrow) => `<!doctype html><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><body style="margin:0">
<script type="module">
import "/panel.js";
const plan = await (await fetch("/plan.json")).json();
${dark ? `document.documentElement.style.cssText = "--primary-background-color:#111;--card-background-color:#1c1c1c;--primary-text-color:#e1e1e1;--secondary-text-color:#9b9b9b;--divider-color:rgba(225,225,225,.12)";` : ""}
window.calls = [];
const el = document.createElement("knx-project-sync-panel");
el.hass = {
  language: "de",
  async callWS(msg) { window.calls.push(msg); return msg.type.endsWith("/plan") ? plan : {}; },
  async fetchWithAuth() { return new Response('{"file_id":"x"}'); },
};
el.narrow = ${narrow};
document.body.append(el);
</script>`;

const server = http
  .createServer((req, res) => {
    const url = new URL(req.url, "http://x");
    if (url.pathname === "/panel.js") res.writeHead(200, { "content-type": "text/javascript" }).end(bundle);
    else if (url.pathname === "/plan.json") res.writeHead(200, { "content-type": "application/json" }).end(plan);
    else res.writeHead(200, { "content-type": "text/html" }).end(page(url.searchParams.has("dark"), url.searchParams.has("narrow")));
  })
  .listen(0);
const base = `http://127.0.0.1:${server.address().port}`;

const browser = await chromium.launch(process.env.PW_CHROMIUM ? { executablePath: process.env.PW_CHROMIUM } : {});
const failures = [];
const check = (ok, what) => {
  if (!ok) failures.push(what);
};
try {
  for (const [name, query, width] of [
    ["light", "", 1200],
    ["dark", "?dark", 1200],
    ["narrow", "?narrow", 390],
  ]) {
    const tab = await browser.newPage({ viewport: { width, height: 900 } });
    const errors = [];
    tab.on("pageerror", (e) => errors.push(e.message));
    tab.on("console", (m) => m.type() === "error" && errors.push(m.text()));
    await tab.goto(`${base}/${query}`);
    await tab.waitForSelector("knx-project-sync-panel >> .row");
    check((await tab.evaluate(() => document.documentElement.scrollWidth)) <= width, `${name}: horizontal scroll`);
    check(await tab.locator("knx-project-sync-panel >> .bar >> text=Übernehmen").isVisible(), `${name}: apply bar`);

    if (name === "light") {
      await tab.click("knx-project-sync-panel >> .chip:has-text('Neu verfügbar')");
      const pending = tab.locator("knx-project-sync-panel >> .row");
      check((await pending.count()) === 3, "pending filter shows 3 rows");
      await pending.first().locator(".check").check();
      await tab.click("knx-project-sync-panel >> .chip:has-text('Alle')");
      const typeSelect = tab.locator("knx-project-sync-panel >> .type select:enabled").first();
      await typeSelect.selectOption("light");
      const name = tab.locator("knx-project-sync-panel >> input.name").nth(1);
      await name.fill("Stehlampe");
      await name.press("Enter");
      await tab.waitForTimeout(400);
      const selection = await tab.evaluate(() => window.calls.at(-1).selection);
      check(Object.values(selection).some((c) => c.enabled === true), "enabled pending entity");
      check(Object.values(selection).some((c) => c.domain === "light"), "type change");
      check(Object.values(selection).some((c) => c.name === "Stehlampe"), "rename");
      await tab.click("knx-project-sync-panel >> .conflict-box button:has-text('In App übernehmen')");
      await tab.locator("knx-project-sync-panel >> button.link:has-text('Schon vorhanden')").first().click();
      await tab.waitForTimeout(400);
      const marked = await tab.evaluate(() => window.calls.at(-1).selection);
      check(Object.values(marked).some((c) => c.adopt === true), "adopt own YAML");
      check(Object.values(marked).some((c) => c.existing === true), "mark as existing");
      // correct a group address by hand
      await tab.locator("knx-project-sync-panel >> button.edit").first().click();
      const ga = tab.locator("knx-project-sync-panel >> .addr input").first();
      await ga.fill("9/x");
      await ga.press("Enter");
      check(await tab.locator("knx-project-sync-panel >> .bar button.primary").isDisabled(), "invalid GA blocks apply");
      await ga.fill("9/9/9");
      await ga.press("Enter");
      await tab.waitForTimeout(400);
      const edited = await tab.evaluate(() => window.calls.at(-1).selection);
      check(Object.values(edited).some((c) => c.addresses && Object.values(c.addresses).includes("9/9/9")), "address edit");
      await tab.click("knx-project-sync-panel >> .bar >> button.primary");
      await tab.waitForTimeout(100);
      const apply = await tab.evaluate(() => window.calls.find((c) => c.type === "knx_project_sync/apply"));
      check(apply && Object.values(apply.selection).some((c) => c.name === "Stehlampe"), "apply sends selection");
    }
    if (process.env.SCREENSHOTS) await tab.screenshot({ path: path.join(process.env.SCREENSHOTS, `${name}.png`) });
    check(errors.length === 0, `${name}: ${errors.join("; ")}`);
    await tab.close();
  }
} finally {
  await browser.close();
  server.close();
}
if (failures.length) {
  console.error(failures.join("\n"));
  process.exit(1);
}
console.log("panel smoke test ok");
