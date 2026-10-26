/**
 * Reference generator: runs the unmodified knx2home pipeline (parseKnxproj +
 * buildHaEntities) on every tests/fixtures/*.knxproj and writes
 *
 *   <name>.manifest.json  golden knx2home-ha-manifest v1 (see docs/manifest-v1.md)
 *
 * The files are deterministic so they can be committed and diffed.
 */
import { execFileSync } from "node:child_process";
import { existsSync, readdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";

import { parseKnxproj } from "@/lib/knx/parse";
import { buildHaEntities, type HaEntities } from "@/lib/knx/export";
import type { KnxCatalog } from "@/lib/types";

const KNX2HOME_DIR = process.env.KNX2HOME_DIR_BUILT as string;
const FIXTURES_DIR = path.resolve(process.argv[2] ?? path.join(__dirname, "../../../tests/fixtures"));

const DOMAINS: Array<[keyof HaEntities, string]> = [
  ["switches", "switch"],
  ["binarySensors", "binary_sensor"],
  ["lights", "light"],
  ["sensors", "sensor"],
  ["times", "time"],
  ["dates", "date"],
  ["datetimes", "datetime"],
  ["covers", "cover"],
  ["scenes", "scene"],
  ["climates", "climate"],
  ["weathers", "weather"],
];

// Field that identifies an entity; the first one present wins.
const PRIMARY_FIELDS: Record<string, string[]> = {
  switch: ["address"],
  binary_sensor: ["state_address"],
  light: ["address", "brightness_address"],
  sensor: ["state_address"],
  time: ["address"],
  date: ["address"],
  datetime: ["address"],
  cover: ["move_long_address", "position_address", "move_short_address", "stop_address"],
  scene: ["address"],
  climate: ["temperature_address", "target_temperature_state_address"],
  weather: ["address_temperature"],
};

type Dict = Record<string, unknown>;

const isAddressField = (key: string) => key === "address" || key.endsWith("_address") || key.startsWith("address_");

/** "1.1" -> "1.001", "DPST-9-1" -> "9.001" */
function canonicalDpt(dpt?: string): string | null {
  if (!dpt) return null;
  const m = dpt.match(/^(?:DPS?T-)?(\d+)(?:[.-](\d+))?$/);
  if (!m) return dpt;
  return m[2] === undefined ? m[1] : `${m[1]}.${m[2].padStart(3, "0")}`;
}

const shortId = (id: string) => id.slice(id.lastIndexOf("_") + 1);

const addressSortKey = (address?: string) =>
  (address ?? "").split("/").map((p) => p.padStart(5, "0")).join("/");

function knx2homeInfo() {
  const pkg = JSON.parse(readFileSync(path.join(KNX2HOME_DIR, "package.json"), "utf8"));
  let commit: string | null = null;
  try {
    commit = execFileSync("git", ["-C", KNX2HOME_DIR, "rev-parse", "HEAD"], { encoding: "utf8" }).trim();
  } catch {
    commit = null;
  }
  return { name: "knx2home", version: String(pkg.version), commit };
}

function buildManifest(catalog: KnxCatalog, ent: HaEntities, generator: Dict) {
  const gaByAddress = new Map(catalog.groupAddresses.flat.map((ga) => [ga.address, ga]));
  const entities: Dict[] = [];

  for (const [listKey, domain] of DOMAINS) {
    const keys = new Map<string, number>();
    const list = (ent[listKey] ?? []) as Dict[];
    const rows = list.map((payload) => {
      const config: Dict = {};
      for (const [k, v] of Object.entries(payload)) if (v !== undefined) config[k] = v;

      const sources: Dict[] = [];
      for (const [field, value] of Object.entries(config)) {
        if (!isAddressField(field) || typeof value !== "string") continue;
        const ga = gaByAddress.get(value);
        sources.push({ field, address: value, ga_id: ga ? shortId(ga.id) : null });
      }
      const primaryField = PRIMARY_FIELDS[domain].find((f) => typeof config[f] === "string")
        ?? (sources[0]?.field as string | undefined);
      const primary = sources.find((s) => s.field === primaryField);
      const base = primary?.ga_id ? `${domain}:${primary.ga_id}` : `${domain}:addr:${primary?.address ?? "none"}`;
      return { base, primaryAddress: primary?.address as string | undefined, config, sources };
    });
    rows.sort((a, b) =>
      addressSortKey(a.primaryAddress).localeCompare(addressSortKey(b.primaryAddress)) ||
      JSON.stringify(a.config).localeCompare(JSON.stringify(b.config))
    );
    for (const row of rows) {
      const n = (keys.get(row.base) ?? 0) + 1;
      keys.set(row.base, n);
      entities.push({
        key: n === 1 ? row.base : `${row.base}#${n}`,
        domain,
        name: (row.config.name as string | undefined) ?? null,
        config: row.config,
        sources: row.sources,
      });
    }
  }

  const unmapped = [...ent.unknowns]
    .sort((a, b) => addressSortKey(a.address).localeCompare(addressSortKey(b.address)))
    .map((u) => {
      const ga = gaByAddress.get(u.address);
      return { address: u.address, ga_id: ga ? shortId(ga.id) : null, name: u.name, dpt: canonicalDpt(u.dpt) };
    });

  return {
    format: "knx2home-ha-manifest",
    version: 1,
    generator,
    project: { name: catalog.meta?.name ?? null },
    options: { drop_reserve: true },
    entities,
    unmapped,
  };
}

const write = (file: string, data: unknown) => writeFileSync(file, JSON.stringify(data, null, 2) + "\n");

async function main() {
  const generator = knx2homeInfo();
  const passwordsFile = path.join(FIXTURES_DIR, "passwords.json");
  const passwords: Record<string, string> = existsSync(passwordsFile)
    ? JSON.parse(readFileSync(passwordsFile, "utf8"))
    : {};
  const fixtures = readdirSync(FIXTURES_DIR).filter((f) => f.endsWith(".knxproj")).sort();
  for (const file of fixtures) {
    const name = file.replace(/\.knxproj$/, "");
    const data = readFileSync(path.join(FIXTURES_DIR, file));
    const catalog = await parseKnxproj(new File([data], file), { password: passwords[name] });
    const ent = buildHaEntities(catalog, { dropReserveFromUnknown: true });
    write(path.join(FIXTURES_DIR, `${name}.manifest.json`), buildManifest(catalog, ent, generator));
    console.log(`${name}: ok`);
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
