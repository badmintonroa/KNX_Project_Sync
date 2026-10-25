/**
 * Sidebar panel of KNX Project Sync: choose which detected entities are created,
 * rename them, correct group addresses and switch between switch and light. Changes are a draft until
 * "Apply"; the backend computes the status of every entity for the draft.
 */
import { LitElement, css, html, nothing, type PropertyValues, type TemplateResult } from "lit";

import { STRINGS, type Strings } from "./strings";

interface Hass {
  language: string;
  locale?: { language: string };
  callWS<T>(msg: Record<string, unknown>): Promise<T>;
  fetchWithAuth(path: string, init?: RequestInit): Promise<Response>;
}

interface Choice {
  enabled?: boolean | null;
  domain?: string | null;
  name?: string | null;
  existing?: boolean | null;
  adopt?: boolean | null;
  config?: Record<string, unknown> | null;
  addresses?: Record<string, string | null> | null;
}
type Selection = Record<string, Choice>;

interface Row {
  key: string;
  status: string;
  reason: string | null;
  domain: string;
  detected_domain: string;
  domains: string[];
  name: string | null;
  ets_name: string | null;
  addresses: { field: string; address: string }[];
  room: string | null;
  in_project: boolean;
  entity_id: string | null;
  previous_domain: string | null;
  selection: Choice;
  suggest_light: boolean;
  conflict_with: {
    domain: string;
    name: string | null;
    file: string | null;
    line: number | null;
    adoptable: boolean;
    kind: "unique_id" | "address" | "app";
    address: string | null;
  } | null;
  adopt: boolean;
  own_config: boolean;
  project_addresses: Record<string, string>;
  address_fields: string[];
}

interface PlanResult {
  project: string | null;
  staged: boolean;
  has_knx_project: boolean;
  has_changes?: boolean;
  last_import: { time: string; project: string | null; source: string } | null;
  stored_selection: Selection;
  domains: string[];
  entities: Row[];
  unmapped: { address: string; name: string; dpt: string | null }[];
  summary: Record<string, number>;
  removed_unique_ids?: number;
}

// three level (1/2/3), two level (1/234) or free (1234) group address
const GA_PATTERN = /^(\d{1,2}\/\d{1,2}\/\d{1,3}|\d{1,2}\/\d{1,4}|\d{1,5})$/;
const WRITTEN = new Set(["new", "changed", "unchanged", "kept"]);
const BLOCKED = new Set(["excluded", "duplicate", "invalid", "conflict", "removed", "existing"]);
const FILTERS = ["all", "active", "pending", "off", "existing", "issues", "gone", "unmapped"] as const;
type Filter = (typeof FILTERS)[number];

/** Not selectable; a GA that is only shared with another entity can still be created on request. */
const isBlocked = (row: Row): boolean =>
  BLOCKED.has(row.status) &&
  !((row.status === "conflict" || row.status === "duplicate") && row.conflict_with && row.conflict_with.kind !== "unique_id");

const inFilter = (row: Row, filter: Filter): boolean => {
  switch (filter) {
    case "all":
      return true;
    case "active":
      return WRITTEN.has(row.status);
    case "pending":
      return row.status === "pending";
    case "existing":
      return row.status === "existing";
    case "off":
      return row.status === "deselected";
    case "issues":
      return ["excluded", "duplicate", "invalid", "conflict"].includes(row.status);
    case "gone":
      return !row.in_project;
    default:
      return false;
  }
};

const clean = (selection: Selection): Selection => {
  const out: Selection = {};
  for (const [key, choice] of Object.entries(selection)) {
    const item: Choice = {};
    if (choice.enabled === true || choice.enabled === false) item.enabled = choice.enabled;
    if (choice.domain) item.domain = choice.domain;
    if (choice.name && choice.name.trim()) item.name = choice.name.trim();
    if (choice.existing) item.existing = true;
    if (choice.adopt) item.adopt = true;
    if (choice.config) item.config = choice.config;
    if (choice.addresses && Object.keys(choice.addresses).length) item.addresses = choice.addresses;
    if (Object.keys(item).length) out[key] = item;
  }
  return out;
};

const sameSelection = (a: Selection, b: Selection) => JSON.stringify(sortKeys(clean(a))) === JSON.stringify(sortKeys(clean(b)));
const sortKeys = (s: Selection) => Object.fromEntries(Object.entries(s).sort(([a], [b]) => a.localeCompare(b)));

class KnxProjectSyncPanel extends LitElement {
  static properties = {
    hass: { attribute: false },
    narrow: { type: Boolean },
    _data: { state: true },
    _draft: { state: true },
    _search: { state: true },
    _filter: { state: true },
    _group: { state: true },
    _busy: { state: true },
    _error: { state: true },
    _message: { state: true },
    _passwordFor: { state: true },
    _showChanges: { state: true },
    _editing: { state: true },
  };

  hass!: Hass;
  narrow = false;
  private _data: PlanResult | null = null;
  private _draft: Selection = {};
  private _search = "";
  private _filter: Filter = "all";
  private _group: "room" | "domain" = "room";
  private _busy: string | null = null;
  private _error: string | null = null;
  private _message: string | null = null;
  private _passwordFor: File | null = null;
  private _showChanges = false;
  private _loaded = false;
  private _timer?: number;
  private _request = 0;
  private _editing = new Set<string>();

  private get t(): Strings {
    const lang = (this.hass?.locale?.language || this.hass?.language || "en").slice(0, 2);
    return STRINGS[lang] ?? STRINGS.en;
  }

  protected updated(changed: PropertyValues): void {
    if (changed.has("hass") && this.hass && !this._loaded) {
      this._loaded = true;
      this._refresh(undefined, true);
      try {
        const saved = JSON.parse(localStorage.getItem("knx-project-sync-view") ?? "{}");
        if (saved.group === "room" || saved.group === "domain") this._group = saved.group;
      } catch {
        /* storage unavailable */
      }
    }
  }

  // ------------------------------------------------------------ backend

  private async _refresh(selection?: Selection, resetDraft = false): Promise<void> {
    const id = ++this._request;
    try {
      const msg: Record<string, unknown> = { type: "knx_project_sync/plan" };
      if (selection) msg.selection = clean(selection);
      const data = await this.hass.callWS<PlanResult>(msg);
      if (id !== this._request) return;
      this._data = data;
      if (resetDraft) this._draft = structuredClone(data.stored_selection ?? {});
      this._error = null;
    } catch (err) {
      if (id === this._request) this._error = this._errorText(err);
    }
  }

  private _scheduleRefresh(): void {
    window.clearTimeout(this._timer);
    this._timer = window.setTimeout(() => this._refresh(this._draft), 250);
  }

  private _errorText(err: unknown): string {
    const e = err as { code?: string; message?: string };
    if (e.code === "adopt_failed") return this.t.adoptFailed(this.t.adoptReasons[e.message ?? ""] ?? e.message ?? "");
    return (e.code && this.t.errors[e.code]) || e.message || String(err);
  }

  private async _loadKnxProject(): Promise<void> {
    await this._run("load", async () => {
      await this.hass.callWS({ type: "knx_project_sync/load_project", source: "knx_project" });
      await this._refresh(this._draft);
      this._message = this.t.loaded;
    });
  }

  private async _upload(file: File, password?: string): Promise<void> {
    await this._run("load", async () => {
      const body = new FormData();
      body.append("file", file);
      const response = await this.hass.fetchWithAuth("/api/file_upload", { method: "POST", body });
      if (!response.ok) throw new Error(`${response.status} ${await response.text()}`);
      const { file_id } = (await response.json()) as { file_id: string };
      try {
        await this.hass.callWS({
          type: "knx_project_sync/load_project",
          source: "upload",
          file_id,
          ...(password ? { password } : {}),
        });
      } catch (err) {
        if ((err as { code?: string }).code === "invalid_password") {
          this._passwordFor = file;
        }
        throw err;
      }
      this._passwordFor = null;
      await this._refresh(this._draft);
      this._message = this.t.loaded;
    });
  }

  private async _discard(): Promise<void> {
    await this._run("discard", async () => {
      if (this._data?.staged) await this.hass.callWS({ type: "knx_project_sync/discard" });
      this._showChanges = false;
      await this._refresh(undefined, true);
    });
  }

  private async _apply(): Promise<void> {
    await this._run("apply", async () => {
      const summary = await this.hass.callWS<Record<string, number>>({
        type: "knx_project_sync/apply",
        selection: clean(this._draft),
      });
      this._showChanges = false;
      await this._refresh(undefined, true);
      this._message = this.t.applied(summary);
    });
  }

  private async _run(what: string, work: () => Promise<void>): Promise<void> {
    this._busy = what;
    this._error = null;
    this._message = null;
    try {
      await work();
    } catch (err) {
      this._error = this._errorText(err);
    } finally {
      this._busy = null;
    }
  }

  // ------------------------------------------------------------ draft

  private _choose(key: string, change: Choice): void {
    const next = { ...(this._draft[key] ?? {}), ...change };
    this._draft = { ...this._draft, [key]: next };
    this._scheduleRefresh();
  }

  private _checked(row: Row): boolean {
    const enabled = this._draft[row.key]?.enabled;
    if (enabled === true || enabled === false) return enabled && !isBlocked(row);
    return WRITTEN.has(row.status);
  }

  private _toggleMany(rows: Row[], on: boolean): void {
    const draft = { ...this._draft };
    for (const row of rows) {
      if (isBlocked(row)) continue;
      draft[row.key] = { ...(draft[row.key] ?? {}), enabled: on };
    }
    this._draft = draft;
    this._scheduleRefresh();
  }

  private get _dirty(): boolean {
    if (!this._data) return false;
    return this._data.staged || !sameSelection(this._draft, this._data.stored_selection ?? {}) || !!this._data.has_changes;
  }

  // ------------------------------------------------------------ rendering

  private _visible(): Row[] {
    const q = this._search.trim().toLowerCase();
    return (this._data?.entities ?? []).filter((row) => {
      if (!inFilter(row, this._filter)) return false;
      if (!q) return true;
      const hay = [row.name, row.ets_name, row.room, row.key, row.entity_id, row.domain, ...row.addresses.map((a) => a.address)]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
      return hay.includes(q);
    });
  }

  protected render(): TemplateResult {
    const t = this.t;
    const data = this._data;
    return html`
      <header class="toolbar">
        ${this.narrow
          ? html`<button class="icon-button" aria-label=${t.menu} @click=${this._toggleMenu}>${icon(ICONS.menu)}</button>`
          : html`<div class="app-icon">${icon(ICONS.home, 20)}</div>`}
        <h1 class="app-title">KNX Project Sync</h1>
        <span class="grow"></span>
        ${data?.has_knx_project
          ? html`<button
              class="secondary tool"
              aria-label=${t.fromKnx}
              title=${t.fromKnx}
              ?disabled=${!!this._busy}
              @click=${this._loadKnxProject}
            >
              ${icon(ICONS.refresh, 18)}<span class="btn-label">${t.fromKnx}</span>
            </button>`
          : nothing}
        <label
          class="button primary tool ${this._busy ? "disabled" : ""}"
          title=${t.upload}
        >
          ${icon(ICONS.upload, 18)}<span class="btn-label">${t.upload}</span>
          <input
            type="file"
            accept=".knxproj"
            class="visually-hidden"
            ?disabled=${!!this._busy}
            @change=${(ev: Event) => {
              const input = ev.target as HTMLInputElement;
              const file = input.files?.[0];
              input.value = "";
              if (file) this._upload(file);
            }}
          />
        </label>
      </header>
      <main class="content">
        ${this._renderProject()}
        ${this._error ? html`<div class="alert error" role="alert">${this._error}</div>` : nothing}
        ${this._message ? html`<div class="alert info" role="status">${this._message}</div>` : nothing}
        ${this._passwordFor ? this._renderPassword() : nothing}
        ${!data
          ? html`<div class="empty">${t.loading}</div>`
          : !data.project
            ? html`<div class="empty">${t.noProject}</div>`
            : html`${this._renderStaged()} ${this._renderStats()} ${this._renderSearch()}
              ${this._filter === "unmapped" ? this._renderUnmapped() : this._renderGroups()}`}
      </main>
      ${data?.project && this._dirty ? this._renderBar() : nothing}
    `;
  }

  private _renderProject(): TemplateResult {
    const t = this.t;
    const data = this._data;
    const last = data?.last_import;
    const time = last ? new Date(last.time).toLocaleString(this.hass.language, { dateStyle: "medium", timeStyle: "short" }) : null;
    return html`<section class="project">
      <div class="eyebrow">${t.eyebrow}</div>
      <h2>${data?.project ?? "–"}</h2>
      <div class="sub">${time ? t.lastImportLine(time, t.sources[last!.source] ?? last!.source) : t.neverImported}</div>
    </section>`;
  }

  private _renderStaged(): TemplateResult | typeof nothing {
    const t = this.t;
    if (!this._data) return nothing;
    // one row per own YAML entry: a climate may cover several detected sensors
    const seen = new Set<string>();
    const adoptable = this._data.entities.filter((r) => {
      const c = r.conflict_with;
      if (r.status !== "conflict" || !c?.adoptable || this._draft[r.key]?.adopt) return false;
      const where = `${c.file}:${c.line}`;
      if (seen.has(where)) return false;
      seen.add(where);
      return true;
    });
    const adoptCard = adoptable.length
      ? html`<section class="staged notice">
          <div class="staged-icon">${icon(ICONS.file, 20)}</div>
          <div class="grow">
            <div class="staged-title">${t.ownYamlTitle(adoptable.length)}</div>
            <div>${t.ownYamlDetail}</div>
          </div>
          <button class="secondary" ?disabled=${!!this._busy} @click=${() => this._adoptAll(adoptable)}>
            ${t.adoptAll(adoptable.length)}
          </button>
        </section>`
      : nothing;
    if (!this._data.last_import && !this._data.staged) {
      return html`<section class="staged notice">
          <div class="staged-icon">${icon(ICONS.light, 20)}</div>
          <div class="grow">
            <div class="staged-title">${t.firstTitle}</div>
            <div>${t.firstDetail}</div>
          </div>
        </section>
        ${adoptCard}`;
    }
    if (!this._data.staged) return adoptCard;
    const rows = this._data.entities;
    const pending = rows.filter((r) => r.status === "pending").length;
    const changed = rows.filter((r) => r.status === "changed").length;
    const gone = rows.filter((r) => !r.in_project).length;
    return html`<section class="staged">
      <div class="staged-icon">${icon(ICONS.file, 20)}</div>
      <div class="grow">
        <div class="staged-title">${t.stagedTitle}</div>
        <div>${t.stagedDetail(pending, changed, gone)}</div>
      </div>
      <button class="text" ?disabled=${!!this._busy} @click=${this._discard}>${t.discardVersion}</button>
    </section>
    ${adoptCard}`;
  }

  private _adoptAll(rows: Row[]): void {
    const draft = { ...this._draft };
    for (const row of rows) draft[row.key] = { ...(draft[row.key] ?? {}), adopt: true };
    this._draft = draft;
    this._scheduleRefresh();
  }

  private _count(f: Filter): number {
    if (f === "unmapped") return this._data?.unmapped.length ?? 0;
    return (this._data?.entities ?? []).filter((r) => inFilter(r, f)).length;
  }

  private _setFilter(f: Filter): void {
    this._filter = this._filter === f ? "all" : f;
  }

  private _renderStats(): TemplateResult {
    const t = this.t;
    const tiles = ["active", "pending", "off", "unmapped"] as const;
    const more = (["existing", "issues", "gone"] as const).filter((f) => this._count(f) > 0 || this._filter === f);
    return html`<section class="stats">
        ${tiles.map((f) => {
          const [label, hint] = f === "active" && !this._data?.last_import ? t.statsSelected : t.stats[f];
          const n = this._count(f);
          return html`<button
            class="stat ${this._filter === f ? "active" : ""} ${f === "pending" && n ? "accent" : ""}"
            aria-pressed=${this._filter === f}
            @click=${() => this._setFilter(f)}
          >
            <span class="stat-label">${label}</span>
            <span class="stat-value"><strong>${n}</strong><span>${hint}</span></span>
          </button>`;
        })}
      </section>
      ${more.length
        ? html`<div class="chips" role="group" aria-label=${t.moreFilters}>
            ${more.map(
              (f) => html`<button class="chip ${this._filter === f ? "active" : ""}" aria-pressed=${this._filter === f} @click=${() => this._setFilter(f)}>
                ${t.filters[f]} <span class="n">${this._count(f)}</span>
              </button>`
            )}
          </div>`
        : nothing}`;
  }

  private _renderSearch(): TemplateResult {
    const t = this.t;
    const setGroup = (group: "room" | "domain") => {
      this._group = group;
      try {
        localStorage.setItem("knx-project-sync-view", JSON.stringify({ group }));
      } catch {
        /* storage unavailable */
      }
    };
    return html`<section class="search-row">
      <label class="search">
        ${icon(ICONS.search, 18)}
        <input
          type="search"
          aria-label=${t.search}
          placeholder=${t.search}
          .value=${this._search}
          @input=${(ev: Event) => (this._search = (ev.target as HTMLInputElement).value)}
        />
      </label>
      <div class="segmented" role="group" aria-label=${t.groupBy}>
        ${(["room", "domain"] as const).map(
          (g) => html`<button aria-pressed=${this._group === g} class=${this._group === g ? "on" : ""} @click=${() => setGroup(g)}>
            ${g === "room" ? t.byRoom : t.byType}
          </button>`
        )}
      </div>
    </section>`;
  }

  private _renderGroups(): TemplateResult {
    const t = this.t;
    const rows = this._visible();
    if (!rows.length) return html`<div class="empty">${t.nothingFound}</div>`;
    const groups = new Map<string, Row[]>();
    for (const row of rows) {
      const name = this._group === "room" ? row.room || t.noRoom : t.domains[row.domain] ?? row.domain;
      groups.set(name, [...(groups.get(name) ?? []), row]);
    }
    const sorted = [...groups.entries()].sort(([a], [b]) =>
      a === t.noRoom ? 1 : b === t.noRoom ? -1 : a.localeCompare(b, this.hass.language)
    );
    return html`${sorted.map(([name, items]) => {
      const choosable = items.filter((r) => !isBlocked(r));
      const on = items.filter((r) => this._checked(r)).length;
      const all = choosable.length > 0 && choosable.every((r) => this._checked(r));
      const progress = items.length ? Math.round((on / items.length) * 100) : 0;
      return html`<section class="room">
        <div class="room-head">
          <h3>${name}</h3>
          <span class="sub">${t.roomCount(on, items.length)}</span>
          <div class="progress" role="progressbar" aria-valuenow=${progress} aria-valuemin="0" aria-valuemax="100" aria-label=${t.roomCount(on, items.length)}>
            <div style="width: ${progress}%"></div>
          </div>
          <button class="secondary small" ?disabled=${!choosable.length} @click=${() => this._toggleMany(choosable, !all)}>
            ${all ? t.allOff : t.allOn}
          </button>
        </div>
        ${items.map((row) => this._renderRow(row))}
      </section>`;
    })}`;
  }

  private _renderRow(row: Row): TemplateResult {
    const t = this.t;
    const choice = this._draft[row.key] ?? {};
    const blocked = isBlocked(row);
    const checked = this._checked(row);
    const domain = choice.domain || row.detected_domain;
    const tone = row.adopt ? "adopt" : row.status;
    const label = row.ets_name ?? row.key;
    return html`<div class="row ${checked ? "" : "off"} ${row.status === "pending" ? "pending" : ""}">
      <button
        class="toggle ${checked ? "on" : ""}"
        role="switch"
        aria-checked=${checked}
        aria-label=${t.create(label)}
        ?disabled=${blocked}
        @click=${() => this._choose(row.key, { enabled: !checked })}
      >
        <span></span>
      </button>
      <div class="tile ${tileClass(row.domain)}">${icon(DOMAIN_ICONS[row.domain] ?? ICONS.generic, 20)}</div>
      <div class="main">
        <label class="name">
          <input
            type="text"
            .value=${choice.name ?? ""}
            placeholder=${label}
            aria-label=${t.name}
            ?disabled=${!row.in_project}
            @change=${(ev: Event) => this._choose(row.key, { name: (ev.target as HTMLInputElement).value })}
          />
          ${row.in_project ? icon(ICONS.pencil, 15) : nothing}
        </label>
        <div class="meta">
          ${row.addresses.map(
            (a) =>
              html`<code class=${row.project_addresses?.[a.field] === a.address ? "" : "edited"} title=${t.fieldLabel(a.field)}
                >${a.address}</code
              >`
          )}
          ${row.in_project && row.address_fields?.length
            ? html`<button
                class="link edit ${this._editing.has(row.key) ? "" : "mark"}"
                aria-expanded=${this._editing.has(row.key)}
                @click=${() => this._toggleEditing(row.key)}
              >
                ${this._editing.has(row.key) ? t.doneAddresses : t.editAddresses}
              </button>`
            : nothing}
          ${this._group === "domain" && row.room ? html`<span>${row.room}</span>` : nothing}
          ${row.entity_id
            ? html`<a href="#" @click=${(ev: Event) => this._moreInfo(ev, row.entity_id!)}>${row.entity_id}</a>`
            : nothing}
        </div>
      </div>
      <div class="type">
        ${row.domains.length > 1
          ? html`<div class="segmented small" role="group" aria-label=${t.type}>
              ${row.domains.map(
                (d) => html`<button
                  class=${d === domain ? "on" : ""}
                  aria-pressed=${d === domain}
                  ?disabled=${blocked}
                  @click=${() => this._choose(row.key, { domain: d })}
                >
                  ${t.domains[d] ?? d}
                </button>`
              )}
            </div>`
          : html`<span class="domain">${t.domains[row.domain] ?? row.domain}</span>`}
        ${row.suggest_light && domain === "switch" && !blocked
          ? html`<button class="hint" title=${t.suggestLightTitle} @click=${() => this._choose(row.key, { domain: "light" })}>
              ${icon(ICONS.light, 14)} ${t.suggestLight}
            </button>`
          : nothing}
      </div>
      <div class="status">
        <span class="pill ${tone}">${this._statusLabel(row)}</span>
        ${row.reason && blocked && !row.conflict_with
          ? html`<span class="reason" title=${row.reason}>${this._reasonLabel(row)}</span>`
          : nothing}
        ${this._renderActions(row, choice)}
      </div>
      ${row.conflict_with ? this._renderConflict(row, choice) : nothing}
      ${this._editing.has(row.key) ? this._renderAddresses(row, choice) : nothing}
    </div>`;
  }

  private _toggleEditing(key: string): void {
    const next = new Set(this._editing);
    if (next.has(key)) next.delete(key);
    else next.add(key);
    this._editing = next;
  }

  /** Current value of an address field in the draft (null = removed). */
  private _address(row: Row, choice: Choice, field: string): string | null {
    const draft = choice.addresses ?? {};
    if (field in draft) return draft[field] ?? null;
    return row.addresses.find((a) => a.field === field)?.address ?? null;
  }

  private _setAddress(row: Row, field: string, value: string | null | undefined): void {
    const addresses = { ...(this._draft[row.key]?.addresses ?? {}) };
    if (value === undefined) delete addresses[field];
    else addresses[field] = value;
    this._choose(row.key, { addresses: Object.keys(addresses).length ? addresses : null });
  }

  /** Correct, add or remove the group addresses of one entity. */
  private _renderAddresses(row: Row, choice: Choice): TemplateResult {
    const t = this.t;
    const draft = choice.addresses ?? {};
    const shown = row.address_fields.filter((f) => this._address(row, choice, f) !== null || f in draft);
    const more = row.address_fields.filter((f) => !shown.includes(f));
    return html`<div class="drawer">
      ${shown.map((field) => {
        const value = this._address(row, choice, field) ?? "";
        const project = row.project_addresses[field];
        const valid = value === "" || GA_PATTERN.test(value);
        const id = `ga-${row.key}-${field}`;
        return html`<div class="addr">
          <label for=${id}>${t.fieldLabel(field)}</label>
          <input
            id=${id}
            type="text"
            inputmode="numeric"
            autocomplete="off"
            spellcheck="false"
            class=${valid ? "" : "invalid"}
            aria-invalid=${!valid}
            .value=${value}
            placeholder=${project ?? "1/2/3"}
            @change=${(ev: Event) => this._setAddress(row, field, (ev.target as HTMLInputElement).value.trim())}
          />
          <span class="addr-note">
            ${!valid
              ? html`<span class="error-text">${t.invalidAddress}</span>`
              : project === undefined
                ? t.addedByHand
                : value === project
                  ? t.fromEts
                  : html`${t.etsValue(project)}
                      <button class="link" @click=${() => this._setAddress(row, field, undefined)}>${t.reset}</button>`}
          </span>
          <button
            class="icon-button small"
            aria-label=${t.removeAddress(t.fieldLabel(field))}
            title=${t.removeAddress(t.fieldLabel(field))}
            @click=${() => this._setAddress(row, field, project === undefined ? undefined : null)}
          >
            ${icon(ICONS.close, 16)}
          </button>
        </div>`;
      })}
      ${more.length
        ? html`<select
            aria-label=${t.addAddress}
            @change=${(ev: Event) => {
              const select = ev.target as HTMLSelectElement;
              if (select.value) this._setAddress(row, select.value, "");
              select.value = "";
            }}
          >
            <option value="">${t.addAddress}</option>
            ${more.map((f) => html`<option value=${f}>${t.fieldLabel(f)}</option>`)}
          </select>`
        : nothing}
    </div>`;
  }

  private get _invalidAddresses(): boolean {
    return Object.values(this._draft).some((c) =>
      Object.values(c.addresses ?? {}).some((v) => v !== null && v !== "" && !GA_PATTERN.test(v))
    );
  }

  /** Own YAML entity on the same GA: where it is and whether it can be taken over. */
  private _renderConflict(row: Row, choice: Choice): TemplateResult {
    const t = this.t;
    const c = row.conflict_with!;
    const where = c.file ? `${c.file}${c.line ? `:${c.line}` : ""}` : t.ownYaml;
    return html`<div class="drawer conflict-box">
      <span class="grow">
        ${row.adopt
          ? t.adoptInfo(where)
          : c.kind === "app"
            ? t.gaInApp(c.address ?? "", t.domains[c.domain] ?? c.domain, c.name ?? "")
            : c.kind === "address"
              ? t.gaInYaml(c.address ?? "", t.domains[c.domain] ?? c.domain, c.name ?? "", where)
              : t.conflictInfo(t.domains[c.domain] ?? c.domain, c.name ?? "", where)}
      </span>
      ${choice.adopt
        ? html`<button class="text" @click=${() => this._choose(row.key, { adopt: null })}>${t.undo}</button>`
        : c.kind === "app"
          ? nothing
          : c.adoptable
          ? html`<button class="secondary small" @click=${() => this._choose(row.key, { adopt: true })}>${t.adopt}</button>`
          : html`<span class="sub">${t.notAdoptable}</span>`}
    </div>`;
  }

  /** Small per-entity actions: already exists elsewhere, back to the project's definition. */
  private _renderActions(row: Row, choice: Choice): TemplateResult | typeof nothing {
    const t = this.t;
    if (!row.in_project) return nothing;
    if (row.status === "existing" || choice.existing) {
      return html`<button class="link" @click=${() => this._choose(row.key, { existing: null })}>${t.undo}</button>`;
    }
    if (row.own_config && choice.config) {
      return html`<button class="link" title=${t.ownConfigTitle} @click=${() => this._choose(row.key, { config: null, domain: null })}>
        ${t.resetConfig}
      </button>`;
    }
    if (BLOCKED.has(row.status) || row.adopt) return nothing;
    return html`<button class="link mark" title=${t.existingTitle} @click=${() => this._choose(row.key, { existing: true })}>
      ${t.markExisting}
    </button>`;
  }

  private _statusLabel(row: Row): string {
    const t = this.t;
    if (row.adopt) return t.status.adopt;
    if (row.reason === "ga_in_use") return t.status.ga_in_use;
    if (row.own_config && row.status === "unchanged") return t.status.own_config;
    if (row.status === "deselected" && row.entity_id) return t.status.deselected_removed;
    if (row.status === "changed" && row.previous_domain && row.previous_domain !== row.domain) return t.status.retyped;
    return t.status[row.status] ?? row.status;
  }

  private _reasonLabel(row: Row): string {
    const t = this.t;
    if (row.reason === "ga_in_use") return t.reasons.ga_in_use;
    if (row.status === "conflict") return t.reasons.own_yaml;
    if (row.status === "duplicate") return row.reason === "light" ? t.reasons.light : t.reasons.unique_id;
    return row.reason ?? "";
  }

  private _renderPassword(): TemplateResult {
    const t = this.t;
    const submit = (ev: Event) => {
      ev.preventDefault();
      const input = this.renderRoot.querySelector<HTMLInputElement>("#password");
      if (this._passwordFor && input) this._upload(this._passwordFor, input.value);
    };
    return html`<form class="alert warn" @submit=${submit}>
      <label for="password" class="grow">${t.passwordNeeded}</label>
      <input id="password" type="password" autocomplete="off" placeholder=${t.password} />
      <button type="submit" class="primary" ?disabled=${!!this._busy}>${t.open}</button>
      <button type="button" class="text" @click=${() => (this._passwordFor = null)}>${t.cancel}</button>
    </form>`;
  }

  private _renderUnmapped(): TemplateResult {
    const t = this.t;
    const q = this._search.trim().toLowerCase();
    const items = (this._data?.unmapped ?? []).filter(
      (u) => !q || `${u.address} ${u.name} ${u.dpt ?? ""}`.toLowerCase().includes(q)
    );
    return html`<p class="sub">${t.unmappedHint}</p>
      <section class="room">
        ${items.map(
          (u) => html`<div class="row unmapped">
            <code>${u.address}</code>
            <div class="main">${u.name}</div>
            <span class="domain">${u.dpt ? `DPT ${u.dpt}` : "–"}</span>
          </div>`
        )}
      </section>`;
  }

  private _renderBar(): TemplateResult {
    const t = this.t;
    const rows = this._data?.entities ?? [];
    const added = rows.filter((r) => r.status === "new" && !r.adopt);
    const adopted = rows.filter((r) => r.adopt);
    const changed = rows.filter((r) => r.status === "changed");
    const removed = rows.filter(
      (r) => r.status === "removed" || ((r.status === "deselected" || r.status === "existing") && r.entity_id)
    );
    const groups: [string, string, Row[]][] = [
      ["add", t.willAdd, added],
      ["change", t.willChange, changed],
      ["remove", t.willRemove, removed],
      ["adopt", t.willAdopt, adopted],
    ];
    return html`<div class="bar-wrap">
      <div class="bar">
        ${this._showChanges
          ? html`<div class="changes">
              ${groups.map(([, label, list]) =>
                list.length
                  ? html`<div>
                      <strong>${label}</strong>
                      <ul>
                        ${list.map((r) => html`<li>${r.name ?? r.key} <span class="dim">(${t.domains[r.domain] ?? r.domain})</span></li>`)}
                      </ul>
                    </div>`
                  : nothing
              )}
            </div>`
          : nothing}
        <div class="bar-main">
          <div class="counts">
            ${groups.map(([kind, , list]) =>
              kind === "adopt" && !list.length
                ? nothing
                : html`<span class="count"><i class="dot ${kind}"></i><strong>${list.length}</strong> ${t.barCounts[kind as "add"]}</span>`
            )}
            <button class="link light" aria-expanded=${this._showChanges} @click=${() => (this._showChanges = !this._showChanges)}>
              ${this._showChanges ? t.hideDetails : t.showDetails}
            </button>
          </div>
          <div class="bar-actions">
            ${this._invalidAddresses ? html`<span class="error-text">${t.fixAddresses}</span>` : nothing}
            <button class="outline" ?disabled=${!!this._busy} @click=${this._discard}>${t.discard}</button>
            <button class="primary" ?disabled=${!!this._busy || this._invalidAddresses} @click=${this._apply}>
              ${this._busy === "apply"
                ? t.applying
                : html`<span class="long">${t.applyLong}</span><span class="short">${t.apply}</span>`}
            </button>
          </div>
        </div>
      </div>
    </div>`;
  }

  private _toggleMenu(): void {
    this.dispatchEvent(new CustomEvent("hass-toggle-menu", { bubbles: true, composed: true }));
  }

  private _moreInfo(ev: Event, entityId: string): void {
    ev.preventDefault();
    this.dispatchEvent(new CustomEvent("hass-more-info", { detail: { entityId }, bubbles: true, composed: true }));
  }

  static styles = css`
    :host {
      --kps-accent: var(--primary-color, #0a6cdb);
      --kps-on-accent: var(--text-primary-color, #fff);
      --kps-ground: var(--primary-background-color, #f4f5f7);
      --kps-surface: var(--card-background-color, #fff);
      --kps-text: var(--primary-text-color, #15171a);
      --kps-muted: var(--secondary-text-color, #5b6270);
      --kps-line: var(--divider-color, rgba(0, 0, 0, 0.12));
      --kps-soft: color-mix(in srgb, var(--kps-text) 6%, transparent);
      --kps-radius: var(--ha-card-border-radius, 16px);
      --kps-success: var(--success-color, #1e9e56);
      --kps-warning: var(--warning-color, #e08600);
      --kps-error: var(--error-color, #d93025);
      --kps-amber: #e8a200;
      --kps-purple: #7b5cd6;
      display: block;
      min-height: 100vh;
      background: var(--kps-ground);
      color: var(--kps-text);
      font-family: var(--ha-font-family-body, Inter, Roboto, system-ui, sans-serif);
      -webkit-font-smoothing: antialiased;
    }
    * {
      box-sizing: border-box;
    }
    h1,
    h2,
    h3 {
      margin: 0;
    }
    .grow {
      flex: 1 1 auto;
      min-width: 0;
    }
    .visually-hidden {
      position: absolute;
      width: 1px;
      height: 1px;
      overflow: hidden;
      clip: rect(0 0 0 0);
      white-space: nowrap;
    }
    svg {
      flex: none;
    }

    /* ---------- controls */
    button,
    .button {
      font: inherit;
      font-size: 14px;
      font-weight: 500;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      height: 40px;
      padding: 0 16px;
      border-radius: 10px;
      border: 1px solid transparent;
      background: none;
      color: var(--kps-text);
      cursor: pointer;
      white-space: nowrap;
    }
    button:disabled,
    .button.disabled {
      opacity: 0.45;
      cursor: default;
    }
    button.primary,
    .button.primary {
      background: var(--kps-accent);
      color: var(--kps-on-accent);
      font-weight: 600;
    }
    button.secondary {
      background: var(--kps-surface);
      border-color: var(--kps-line);
    }
    button.small {
      height: 32px;
      padding: 0 12px;
      font-size: 13px;
      border-radius: 8px;
    }
    button.text {
      color: inherit;
      padding: 0 12px;
    }
    .short {
      display: none;
    }
    .icon-button {
      width: 44px;
      height: 44px;
      padding: 0;
      border-radius: 10px;
    }
    .icon-button.small {
      width: 32px;
      height: 32px;
      color: var(--kps-muted);
    }
    button.link {
      height: auto;
      padding: 2px 0;
      border-radius: 4px;
      font-size: 12px;
      color: var(--kps-accent);
    }
    input[type="text"],
    input[type="password"],
    select {
      font: inherit;
      font-size: 14px;
      color: var(--kps-text);
      background: var(--kps-surface);
      border: 1px solid var(--kps-line);
      border-radius: 8px;
      height: 36px;
      padding: 0 10px;
      min-width: 0;
    }
    :focus-visible {
      outline: 2px solid var(--kps-accent);
      outline-offset: 2px;
    }
    .sub {
      color: var(--kps-muted);
      font-size: 14px;
    }
    code {
      font-family: var(--ha-font-family-code, "JetBrains Mono", ui-monospace, monospace);
      font-size: 12px;
      background: var(--kps-soft);
      border-radius: 6px;
      padding: 2px 7px;
    }
    code.edited {
      background: color-mix(in srgb, var(--kps-warning) 18%, transparent);
      box-shadow: inset 0 0 0 1px var(--kps-warning);
    }

    /* ---------- toolbar */
    .toolbar {
      position: sticky;
      top: 0;
      z-index: 5;
      display: flex;
      align-items: center;
      gap: 12px;
      height: var(--header-height, 64px);
      padding: 0 24px;
      background: var(--kps-surface);
      border-bottom: 1px solid var(--kps-line);
    }
    .app-icon {
      width: 34px;
      height: 34px;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: var(--kps-accent);
      color: var(--kps-on-accent);
    }
    .app-title {
      font-size: 18px;
      font-weight: 600;
      letter-spacing: -0.01em;
    }

    /* ---------- content */
    .content {
      max-width: 1120px;
      margin: 0 auto;
      padding: 32px 24px 24px;
      display: flex;
      flex-direction: column;
      gap: 20px;
    }
    .project {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    .eyebrow {
      font-size: 12px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: var(--kps-muted);
    }
    .project h2 {
      font-size: 32px;
      font-weight: 700;
      letter-spacing: -0.02em;
    }
    .alert {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 10px;
      padding: 12px 16px;
      border-radius: 12px;
      background: var(--kps-surface);
      border: 1px solid var(--kps-line);
    }
    .alert.error {
      border-color: var(--kps-error);
      color: var(--kps-error);
    }
    .alert.info {
      border-color: var(--kps-accent);
    }
    .staged {
      display: flex;
      align-items: center;
      gap: 14px;
      padding: 14px 18px;
      border-radius: 14px;
      background: color-mix(in srgb, var(--kps-warning) 12%, var(--kps-surface));
      border: 1px solid color-mix(in srgb, var(--kps-warning) 40%, transparent);
      font-size: 14px;
    }
    .staged > .grow {
      flex: 1 1 0;
    }
    .staged.notice {
      background: color-mix(in srgb, var(--kps-accent) 8%, var(--kps-surface));
      border-color: color-mix(in srgb, var(--kps-accent) 35%, transparent);
    }
    .staged.notice .staged-icon {
      background: color-mix(in srgb, var(--kps-accent) 18%, transparent);
      color: var(--kps-accent);
    }
    .staged-icon {
      width: 36px;
      height: 36px;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: color-mix(in srgb, var(--kps-warning) 22%, transparent);
      color: var(--kps-warning);
    }
    .staged-title {
      font-size: 15px;
      font-weight: 600;
      margin-bottom: 2px;
    }
    .stats {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 16px;
    }
    .stat {
      height: auto;
      flex-direction: column;
      align-items: flex-start;
      justify-content: flex-start;
      gap: 6px;
      padding: 16px 18px;
      background: var(--kps-surface);
      border: 1px solid var(--kps-line);
      border-radius: 14px;
      text-align: left;
      white-space: normal;
    }
    .stat.accent {
      border-color: var(--kps-accent);
    }
    .stat.active {
      box-shadow: inset 0 0 0 2px var(--kps-accent);
      border-color: var(--kps-accent);
    }
    .stat-label {
      font-size: 13px;
      color: var(--kps-muted);
    }
    .stat-value {
      display: flex;
      align-items: baseline;
      gap: 8px;
      font-size: 13px;
      color: var(--kps-muted);
    }
    .stat-value strong {
      font-size: 28px;
      font-weight: 700;
      letter-spacing: -0.02em;
      color: var(--kps-text);
    }
    .stat.accent strong {
      color: var(--kps-accent);
    }
    .chips {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: -8px;
    }
    .chip {
      height: 32px;
      padding: 0 12px;
      border-radius: 16px;
      border-color: var(--kps-line);
      background: var(--kps-surface);
      font-size: 13px;
    }
    .chip.active {
      background: var(--kps-text);
      color: var(--kps-surface);
    }
    .chip .n {
      opacity: 0.7;
    }
    .search-row {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
    }
    .search {
      flex: 1 1 200px;
      display: flex;
      align-items: center;
      gap: 10px;
      height: 44px;
      padding: 0 14px;
      background: var(--kps-surface);
      border: 1px solid var(--kps-line);
      border-radius: 12px;
      color: var(--kps-muted);
    }
    .search:focus-within {
      border-color: var(--kps-accent);
    }
    .search input {
      font: inherit;
      font-size: 15px;
      flex: 1;
      min-width: 0;
      border: none;
      outline: none;
      background: transparent;
      color: var(--kps-text);
    }
    .segmented {
      display: inline-flex;
      gap: 4px;
      padding: 4px;
      border-radius: 12px;
      background: var(--kps-soft);
    }
    .segmented button {
      height: 36px;
      padding: 0 14px;
      border-radius: 9px;
      color: var(--kps-muted);
    }
    .segmented button.on {
      background: var(--kps-surface);
      color: var(--kps-text);
      font-weight: 600;
      box-shadow: 0 1px 2px rgba(16, 24, 40, 0.12);
    }
    .segmented.small {
      padding: 3px;
      gap: 3px;
      border-radius: 10px;
    }
    .segmented.small button {
      height: 32px;
      padding: 0 12px;
      font-size: 13px;
      border-radius: 8px;
    }

    /* ---------- rooms and rows */
    .room {
      background: var(--kps-surface);
      border: 1px solid var(--ha-card-border-color, var(--kps-line));
      border-radius: var(--kps-radius);
      box-shadow: var(--ha-card-box-shadow, 0 1px 2px rgba(16, 24, 40, 0.04));
      overflow: hidden;
    }
    .room-head {
      display: flex;
      align-items: center;
      gap: 14px;
      padding: 14px 20px;
      flex-wrap: wrap;
    }
    .room-head h3 {
      font-size: 17px;
      font-weight: 600;
      flex: 1 1 auto;
    }
    .room-head .sub {
      font-size: 13px;
    }
    .progress {
      width: 96px;
      height: 6px;
      border-radius: 3px;
      background: var(--kps-soft);
      overflow: hidden;
    }
    .progress div {
      height: 100%;
      border-radius: 3px;
      background: var(--kps-accent);
      transition: width 0.2s;
    }
    .row {
      display: grid;
      grid-template-columns: 48px 40px minmax(0, 1fr) 210px 170px;
      align-items: center;
      gap: 10px 16px;
      padding: 14px 20px;
      border-top: 1px solid var(--kps-line);
    }
    .row.pending {
      background: color-mix(in srgb, var(--kps-accent) 5%, transparent);
    }
    .row.off .tile,
    .row.off .main {
      opacity: 0.6;
    }
    .row.unmapped {
      grid-template-columns: 90px minmax(0, 1fr) auto;
    }
    .toggle {
      width: 44px;
      height: 26px;
      padding: 3px;
      border-radius: 13px;
      background: color-mix(in srgb, var(--kps-text) 24%, transparent);
      justify-content: flex-start;
      transition: background 0.15s;
    }
    .toggle span {
      width: 20px;
      height: 20px;
      border-radius: 50%;
      background: #fff;
      box-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
      transition: transform 0.15s;
    }
    .toggle.on {
      background: var(--kps-accent);
    }
    .toggle.on span {
      transform: translateX(18px);
    }
    .tile {
      width: 40px;
      height: 40px;
      border-radius: 11px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: var(--kps-tile);
      background: color-mix(in srgb, var(--kps-tile) 15%, transparent);
    }
    .tile.light {
      --kps-tile: var(--kps-amber);
    }
    .tile.switch {
      --kps-tile: var(--kps-accent);
    }
    .tile.sensor {
      --kps-tile: var(--kps-success);
    }
    .tile.cover {
      --kps-tile: var(--kps-purple);
    }
    .tile.other {
      --kps-tile: var(--kps-muted);
    }
    .main {
      min-width: 0;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    .name {
      display: flex;
      align-items: center;
      gap: 8px;
      color: var(--kps-muted);
    }
    .name input {
      font: inherit;
      font-size: 15px;
      font-weight: 600;
      color: var(--kps-text);
      background: transparent;
      border: none;
      border-bottom: 1px dashed var(--kps-line);
      border-radius: 0;
      padding: 2px 0;
      flex: 1;
      min-width: 0;
    }
    .name input::placeholder {
      color: var(--kps-text);
      opacity: 1;
    }
    .name input:focus {
      outline: none;
      border-bottom: 1px solid var(--kps-accent);
    }
    .meta {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 6px;
      font-size: 12px;
      color: var(--kps-muted);
    }
    .meta a {
      color: var(--kps-accent);
      text-decoration: none;
    }
    .type {
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      gap: 6px;
    }
    .domain {
      font-size: 14px;
      font-weight: 500;
    }
    .hint {
      height: 28px;
      padding: 0 10px;
      font-size: 12px;
      font-weight: 600;
      border-radius: 8px;
      gap: 6px;
      color: color-mix(in srgb, var(--kps-amber) 65%, var(--kps-text));
      background: color-mix(in srgb, var(--kps-amber) 16%, transparent);
    }
    .status {
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      gap: 4px;
      text-align: right;
      min-width: 0;
    }
    .pill {
      --kps-tone: var(--kps-muted);
      font-size: 12px;
      font-weight: 600;
      padding: 4px 10px;
      border-radius: 999px;
      white-space: nowrap;
      color: color-mix(in srgb, var(--kps-tone) 75%, var(--kps-text));
      background: color-mix(in srgb, var(--kps-tone) 16%, transparent);
    }
    .pill.unchanged,
    .pill.kept {
      --kps-tone: var(--kps-success);
    }
    .pill.new,
    .pill.adopt {
      --kps-tone: var(--kps-accent);
    }
    .pill.pending {
      background: var(--kps-accent);
      color: var(--kps-on-accent);
    }
    .pill.changed {
      --kps-tone: var(--kps-warning);
    }
    .pill.removed,
    .pill.invalid {
      --kps-tone: var(--kps-error);
    }
    .reason {
      font-size: 12px;
      color: var(--kps-muted);
      max-width: 100%;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    @media (hover: hover) {
      .row .mark {
        opacity: 0;
      }
      .row:hover .mark,
      .row:focus-within .mark {
        opacity: 1;
      }
    }
    .drawer {
      grid-column: 3 / -1;
      display: flex;
      flex-direction: column;
      gap: 8px;
      padding: 12px 14px;
      border-radius: 12px;
      background: var(--kps-soft);
      font-size: 13px;
    }
    .conflict-box {
      flex-direction: row;
      flex-wrap: wrap;
      align-items: center;
    }
    .addr {
      display: grid;
      grid-template-columns: 170px 130px minmax(0, 1fr) auto;
      align-items: center;
      gap: 6px 12px;
    }
    .addr input {
      font-family: var(--ha-font-family-code, ui-monospace, monospace);
    }
    .addr input.invalid {
      border-color: var(--kps-error);
    }
    .addr-note {
      color: var(--kps-muted);
      font-size: 12px;
    }
    .drawer select {
      align-self: flex-start;
    }
    .error-text {
      color: var(--kps-error);
      font-size: 12px;
    }
    .empty {
      padding: 48px 16px;
      text-align: center;
      color: var(--kps-muted);
    }

    /* ---------- apply bar (inverted colours, also in dark themes) */
    .bar-wrap {
      position: sticky;
      bottom: 16px;
      z-index: 4;
      max-width: 1120px;
      margin: 0 auto 16px;
      padding: 0 24px;
    }
    .bar {
      --kps-bar-text: var(--kps-surface);
      background: var(--kps-text);
      color: var(--kps-bar-text);
      border-radius: 16px;
      box-shadow: 0 12px 32px rgba(16, 24, 40, 0.24);
    }
    .bar-main {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 12px 18px;
      padding: 12px 14px 12px 22px;
    }
    .counts {
      flex: 1 1 auto;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 6px 18px;
      font-size: 14px;
    }
    .count {
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }
    .dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--kps-accent);
    }
    .dot.change {
      background: var(--kps-warning);
    }
    .dot.remove {
      background: var(--kps-error);
    }
    .dim {
      opacity: 0.7;
    }
    .bar button.link.light {
      color: inherit;
      opacity: 0.8;
      text-decoration: underline;
      font-size: 14px;
    }
    .bar-actions {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-left: auto;
    }
    .bar button.outline {
      color: inherit;
      border-color: color-mix(in srgb, var(--kps-bar-text) 30%, transparent);
      height: 44px;
    }
    .bar button.primary {
      height: 44px;
      padding: 0 20px;
    }
    .bar .error-text {
      color: inherit;
    }
    .changes {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 12px;
      max-height: 40vh;
      overflow: auto;
      padding: 16px 22px 0;
      font-size: 14px;
    }
    .changes ul {
      margin: 4px 0 0;
      padding-left: 18px;
    }

    /* ---------- phone */
    @media (max-width: 760px) {
      .btn-label,
      .long,
      .app-icon {
        display: none;
      }
      .short {
        display: inline;
      }
      .tool {
        width: 44px;
        height: 44px;
        padding: 0;
      }
      .app-title {
        font-size: 17px;
      }
      .toolbar {
        padding: 0 8px 0 4px;
        gap: 4px;
      }
      .content {
        padding: 16px 16px 16px;
        gap: 14px;
      }
      .project h2 {
        font-size: 22px;
      }
      .staged {
        flex-wrap: wrap;
      }
      .staged > .grow {
        flex-basis: calc(100% - 60px);
      }
      .stats {
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 10px;
      }
      .stat {
        padding: 12px 14px;
      }
      .stat-value strong {
        font-size: 22px;
      }
      .room-head {
        padding: 12px 14px;
      }
      .progress {
        width: 56px;
      }
      .row {
        grid-template-columns: 36px minmax(0, 1fr) auto 48px;
        grid-template-areas:
          "tile main main toggle"
          ". type status status";
        padding: 12px 14px;
        gap: 10px 12px;
      }
      .tile {
        grid-area: tile;
        width: 36px;
        height: 36px;
      }
      .main {
        grid-area: main;
      }
      .toggle {
        grid-area: toggle;
        justify-self: end;
      }
      .type {
        grid-area: type;
        flex-direction: row;
        flex-wrap: wrap;
        align-items: center;
      }
      .status {
        grid-area: status;
      }
      .drawer {
        grid-column: 1 / -1;
      }
      .addr {
        grid-template-columns: minmax(0, 1fr) auto;
      }
      .addr label {
        grid-column: 1 / -1;
      }
      .addr-note {
        grid-column: 1 / -1;
      }
      .bar-wrap {
        padding: 0 12px;
      }
      .bar-main {
        padding: 12px;
      }
      .counts {
        gap: 4px 12px;
        font-size: 13px;
      }
      .segmented button {
        padding: 0 10px;
      }
    }
  `;
}

// ---------------------------------------------------------------- icons (24px stroke paths)

const ICONS = {
  menu: "M4 6h16M4 12h16M4 18h16",
  home: "M3 10.5 12 4l9 6.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z",
  refresh: "M3 12a9 9 0 0 1 15.5-6.2L21 8M21 3v5h-5M21 12a9 9 0 0 1-15.5 6.2L3 16M3 21v-5h5",
  upload: "M12 16V4M7 9l5-5 5 5M4 20h16",
  search: "M11 4a7 7 0 1 0 0 14 7 7 0 0 0 0-14zM21 21l-4.35-4.35",
  file: "M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8zM14 3v5h5M12 18v-6M9 15l3 3 3-3",
  pencil: "M12 20h9M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z",
  close: "M6 6l12 12M18 6 6 18",
  light: "M9 18h6M10 22h4M12 2a7 7 0 0 0-4 12.7c.6.5 1 1.3 1 2.1V17h6v-.2c0-.8.4-1.6 1-2.1A7 7 0 0 0 12 2z",
  switch: "M8 7h8a5 5 0 0 1 0 10H8A5 5 0 0 1 8 7zM8 9.5a2.5 2.5 0 1 0 0 5 2.5 2.5 0 0 0 0-5z",
  sensor: "M14 14.76V3.5a2.5 2.5 0 0 0-5 0v11.26a4.5 4.5 0 1 0 5 0z",
  cover: "M4 3h16M5 3v14M19 3v14M5 7h14M5 11h14M5 15h14M12 17v4",
  binary: "M6 3h9v18H6zM15 5h3v16M12 12h.01",
  scene: "M12 3l2.6 5.6 6 .7-4.5 4.1 1.2 6L12 16.4 6.7 19.4l1.2-6L3.4 9.3l6-.7z",
  climate: "M12 3v18M5.6 6.6l12.8 10.8M18.4 6.6 5.6 17.4M3 12h18",
  weather: "M12 3v2M5.6 5.6 7 7M3 12h2M17 7l1.4-1.4M16 12a4 4 0 1 0-6.9 2.8M8 19h9a3 3 0 0 0 0-6 4.5 4.5 0 0 0-8.6 1.4A2.4 2.4 0 0 0 8 19z",
  clock: "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zM12 7v5l3 2",
  generic: "M4 4h16v16H4zM9 9h6v6H9z",
  text: "M4 7V5h16v2M9 19h6M12 5v14",
} as const;

const DOMAIN_ICONS: Record<string, string> = {
  light: ICONS.light,
  switch: ICONS.switch,
  sensor: ICONS.sensor,
  binary_sensor: ICONS.binary,
  cover: ICONS.cover,
  scene: ICONS.scene,
  climate: ICONS.climate,
  weather: ICONS.weather,
  time: ICONS.clock,
  date: ICONS.clock,
  datetime: ICONS.clock,
  text: ICONS.text,
};

const tileClass = (domain: string): string =>
  domain === "light" || domain === "switch" || domain === "cover"
    ? domain
    : domain === "sensor" || domain === "climate" || domain === "weather"
      ? "sensor"
      : "other";

const icon = (path: string, size = 22) => html`<svg width=${size} height=${size} viewBox="0 0 24 24" fill="none"
  stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d=${path}></path></svg>`;

customElements.define("knx-project-sync-panel", KnxProjectSyncPanel);
