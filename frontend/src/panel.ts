/**
 * Sidebar panel of KNX Project Sync: choose which detected entities are created,
 * rename them and switch between switch and light. Changes are a draft until
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
  conflict_with: { domain: string; name: string | null; file: string | null; line: number | null; adoptable: boolean } | null;
  adopt: boolean;
  own_config: boolean;
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

const WRITTEN = new Set(["new", "changed", "unchanged", "kept"]);
const BLOCKED = new Set(["excluded", "duplicate", "invalid", "conflict", "removed", "existing"]);
const FILTERS = ["all", "active", "pending", "off", "existing", "issues", "gone", "unmapped"] as const;
type Filter = (typeof FILTERS)[number];

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
    if (enabled === true || enabled === false) return enabled && !BLOCKED.has(row.status);
    return WRITTEN.has(row.status);
  }

  private _toggleMany(rows: Row[], on: boolean): void {
    const draft = { ...this._draft };
    for (const row of rows) {
      if (BLOCKED.has(row.status)) continue;
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
      <div class="toolbar">
        ${this.narrow
          ? html`<button class="icon" title=${t.menu} @click=${this._toggleMenu}>
              <svg viewBox="0 0 24 24"><path d="M3,6H21V8H3V6M3,11H21V13H3V11M3,16H21V18H3V16Z" /></svg>
            </button>`
          : nothing}
        <div class="title">KNX Project Sync</div>
      </div>
      <div class="content">
        ${this._renderHeader()} ${this._error ? html`<div class="alert error">${this._error}</div>` : nothing}
        ${this._message ? html`<div class="alert info">${this._message}</div>` : nothing}
        ${this._passwordFor ? this._renderPassword() : nothing}
        ${!data
          ? html`<div class="empty">${t.loading}</div>`
          : !data.project
            ? html`<div class="empty">${t.noProject}</div>`
            : html`${this._renderFilters()} ${this._filter === "unmapped" ? this._renderUnmapped() : this._renderGroups()}`}
      </div>
      ${data?.project && this._dirty ? this._renderBar() : nothing}
    `;
  }

  private _renderHeader(): TemplateResult {
    const t = this.t;
    const data = this._data;
    const last = data?.last_import;
    return html`
      <div class="header">
        <div>
          <div class="project">${data?.project ?? "–"}</div>
          <div class="sub">
            ${last ? t.lastImport(new Date(last.time).toLocaleString(this.hass.language)) : t.neverImported}
            ${data ? html` · ${t.count(data.entities.filter((r) => WRITTEN.has(r.status)).length)}` : nothing}
          </div>
        </div>
        <div class="actions">
          ${data?.has_knx_project
            ? html`<button ?disabled=${!!this._busy} @click=${this._loadKnxProject}>${t.fromKnx}</button>`
            : nothing}
          <label class="button ${this._busy ? "disabled" : ""}">
            ${t.upload}
            <input
              type="file"
              accept=".knxproj"
              hidden
              ?disabled=${!!this._busy}
              @change=${(ev: Event) => {
                const input = ev.target as HTMLInputElement;
                const file = input.files?.[0];
                input.value = "";
                if (file) this._upload(file);
              }}
            />
          </label>
        </div>
      </div>
      ${data?.staged
        ? html`<div class="alert warn">
            <span>${t.staged}</span>
            <button class="text" @click=${this._discard}>${t.discardProject}</button>
          </div>`
        : nothing}
    `;
  }

  private _renderPassword(): TemplateResult {
    const t = this.t;
    const submit = (ev: Event) => {
      ev.preventDefault();
      const input = this.renderRoot.querySelector<HTMLInputElement>("#password");
      if (this._passwordFor && input) this._upload(this._passwordFor, input.value);
    };
    return html`<form class="alert warn" @submit=${submit}>
      <span>${t.passwordNeeded}</span>
      <input id="password" type="password" autocomplete="off" placeholder=${t.password} />
      <button type="submit" ?disabled=${!!this._busy}>${t.open}</button>
      <button type="button" class="text" @click=${() => (this._passwordFor = null)}>${t.cancel}</button>
    </form>`;
  }

  private _renderFilters(): TemplateResult {
    const t = this.t;
    const rows = this._data?.entities ?? [];
    const count = (f: Filter) => (f === "unmapped" ? this._data?.unmapped.length ?? 0 : rows.filter((r) => inFilter(r, f)).length);
    return html`
      <div class="filters">
        <input
          class="search"
          type="search"
          placeholder=${t.search}
          .value=${this._search}
          @input=${(ev: Event) => (this._search = (ev.target as HTMLInputElement).value)}
        />
        <select
          aria-label=${t.groupBy}
          .value=${this._group}
          @change=${(ev: Event) => {
            this._group = (ev.target as HTMLSelectElement).value as "room" | "domain";
            try {
              localStorage.setItem("knx-project-sync-view", JSON.stringify({ group: this._group }));
            } catch {
              /* storage unavailable */
            }
          }}
        >
          <option value="room">${t.byRoom}</option>
          <option value="domain">${t.byType}</option>
        </select>
      </div>
      <div class="chips" role="tablist">
        ${FILTERS.map((f) => {
          const n = count(f);
          if (n === 0 && f !== "all" && f !== this._filter) return nothing;
          return html`<button
            role="tab"
            class="chip ${f === this._filter ? "active" : ""} ${f === "pending" ? "accent" : ""}"
            aria-selected=${f === this._filter}
            @click=${() => (this._filter = f)}
          >
            ${t.filters[f]} <span class="n">${n}</span>
          </button>`;
        })}
      </div>
    `;
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
      const choosable = items.filter((r) => !BLOCKED.has(r.status));
      const on = choosable.filter((r) => this._checked(r)).length;
      return html`<section class="group">
        <div class="group-head">
          <input
            type="checkbox"
            aria-label=${t.selectGroup(name)}
            .checked=${choosable.length > 0 && on === choosable.length}
            .indeterminate=${on > 0 && on < choosable.length}
            ?disabled=${!choosable.length}
            @change=${(ev: Event) => this._toggleMany(choosable, (ev.target as HTMLInputElement).checked)}
          />
          <h2>${name}</h2>
          <span class="n">${on}/${items.length}</span>
        </div>
        <div class="rows">${items.map((row) => this._renderRow(row))}</div>
      </section>`;
    })}`;
  }

  private _renderRow(row: Row): TemplateResult {
    const t = this.t;
    const choice = this._draft[row.key] ?? {};
    const blocked = BLOCKED.has(row.status);
    const checked = this._checked(row);
    const domain = choice.domain || row.detected_domain;
    return html`<div class="row ${checked ? "" : "off"} ${blocked ? "blocked" : ""}">
      <input
        type="checkbox"
        class="check"
        aria-label=${t.create(row.ets_name ?? row.key)}
        .checked=${checked}
        ?disabled=${blocked}
        @change=${(ev: Event) => this._choose(row.key, { enabled: (ev.target as HTMLInputElement).checked })}
      />
      <div class="main">
        <input
          class="name"
          type="text"
          .value=${choice.name ?? ""}
          placeholder=${row.ets_name ?? row.key}
          aria-label=${t.name}
          ?disabled=${!row.in_project}
          @change=${(ev: Event) => this._choose(row.key, { name: (ev.target as HTMLInputElement).value })}
        />
        <div class="meta">
          ${row.addresses.map((a) => html`<code title=${a.field}>${a.address}</code>`)}
          ${this._group === "domain" && row.room ? html`<span>${row.room}</span>` : nothing}
          ${row.entity_id
            ? html`<a href="#" @click=${(ev: Event) => this._moreInfo(ev, row.entity_id!)}>${row.entity_id}</a>`
            : nothing}
        </div>
      </div>
      <div class="type">
        ${row.domains.length > 1
          ? html`<select
              aria-label=${t.type}
              ?disabled=${blocked}
              .value=${domain}
              @change=${(ev: Event) => this._choose(row.key, { domain: (ev.target as HTMLSelectElement).value })}
            >
              ${row.domains.map((d) => html`<option value=${d} ?selected=${d === domain}>${t.domains[d] ?? d}</option>`)}
            </select>`
          : html`<span class="domain">${t.domains[row.domain] ?? row.domain}</span>`}
        ${row.suggest_light && domain === "switch" && !blocked
          ? html`<button class="hint" title=${t.suggestLightTitle} @click=${() => this._choose(row.key, { domain: "light" })}>
              ${t.suggestLight}
            </button>`
          : nothing}
      </div>
      <div class="status">
        <span class="badge ${row.adopt ? "adopt" : row.status}">${this._statusLabel(row)}</span>
        ${row.reason && blocked && !row.conflict_with
          ? html`<div class="reason" title=${row.reason}>${this._reasonLabel(row)}</div>`
          : nothing}
        ${this._renderActions(row, choice)}
      </div>
      ${row.conflict_with ? this._renderConflict(row, choice) : nothing}
    </div>`;
  }

  /** Own YAML entity on the same GA: where it is and whether it can be taken over. */
  private _renderConflict(row: Row, choice: Choice): TemplateResult {
    const t = this.t;
    const c = row.conflict_with!;
    const where = c.file ? `${c.file}${c.line ? `:${c.line}` : ""}` : t.ownYaml;
    return html`<div class="conflict-box">
      <span>
        ${row.adopt ? t.adoptInfo(where) : t.conflictInfo(t.domains[c.domain] ?? c.domain, c.name ?? "", where)}
      </span>
      ${choice.adopt
        ? html`<button class="text" @click=${() => this._choose(row.key, { adopt: null })}>${t.undo}</button>`
        : c.adoptable
          ? html`<button @click=${() => this._choose(row.key, { adopt: true })}>${t.adopt}</button>`
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
    if (row.status === "conflict" || BLOCKED.has(row.status) || row.adopt) return nothing;
    return html`<button class="link mark" title=${t.existingTitle} @click=${() => this._choose(row.key, { existing: true })}>
      ${t.markExisting}
    </button>`;
  }

  private _statusLabel(row: Row): string {
    const t = this.t;
    if (row.adopt) return t.status.adopt;
    if (row.own_config && row.status === "unchanged") return t.status.own_config;
    if (row.status === "deselected" && row.entity_id) return t.status.deselected_removed;
    if (row.status === "changed" && row.previous_domain && row.previous_domain !== row.domain) return t.status.retyped;
    return t.status[row.status] ?? row.status;
  }

  private _reasonLabel(row: Row): string {
    const t = this.t;
    if (row.status === "conflict") return t.reasons.own_yaml;
    if (row.status === "duplicate") return row.reason === "light" ? t.reasons.light : t.reasons.unique_id;
    return row.reason ?? "";
  }

  private _renderUnmapped(): TemplateResult {
    const t = this.t;
    const q = this._search.trim().toLowerCase();
    const items = (this._data?.unmapped ?? []).filter(
      (u) => !q || `${u.address} ${u.name} ${u.dpt ?? ""}`.toLowerCase().includes(q)
    );
    return html`<p class="sub">${t.unmappedHint}</p>
      <div class="rows">
        ${items.map(
          (u) => html`<div class="row off unmapped">
            <code>${u.address}</code>
            <div class="main">${u.name}</div>
            <span class="domain">${u.dpt ? `DPT ${u.dpt}` : "–"}</span>
          </div>`
        )}
      </div>`;
  }

  private _renderBar(): TemplateResult {
    const t = this.t;
    const s = this._data?.summary ?? {};
    const rows = this._data?.entities ?? [];
    const added = rows.filter((r) => r.status === "new" && !r.adopt);
    const adopted = rows.filter((r) => r.adopt);
    const changed = rows.filter((r) => r.status === "changed");
    const removed = rows.filter(
      (r) => r.status === "removed" || ((r.status === "deselected" || r.status === "existing") && r.entity_id)
    );
    return html`<div class="bar">
      ${this._showChanges
        ? html`<div class="changes">
            ${[
              [t.willAdd, added],
              [t.willChange, changed],
              [t.willRemove, removed],
              [t.willAdopt, adopted],
            ].map(([label, list]) =>
              (list as Row[]).length
                ? html`<div>
                    <strong>${label as string}</strong>
                    <ul>
                      ${(list as Row[]).map((r) => html`<li>${r.name ?? r.key} <span class="sub">(${t.domains[r.domain] ?? r.domain})</span></li>`)}
                    </ul>
                  </div>`
                : nothing
            )}
          </div>`
        : nothing}
      <div class="bar-main">
        <div class="bar-info">
          <button
            class="text summary"
            aria-expanded=${this._showChanges}
            @click=${() => (this._showChanges = !this._showChanges)}
          >
            ${t.summary(added.length, changed.length, removed.length)}${adopted.length ? ` · ${t.adoptCount(adopted.length)}` : ""} ${this._showChanges ? "▾" : "▴"}
          </button>
          ${s.pending ? html`<span class="sub">${t.stillPending(s.pending)}</span>` : nothing}
        </div>
        <div class="bar-actions">
          <button class="text" ?disabled=${!!this._busy} @click=${this._discard}>${t.discard}</button>
          <button class="primary" ?disabled=${!!this._busy} @click=${this._apply}>
            ${this._busy === "apply" ? t.applying : t.apply}
          </button>
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
      display: block;
      min-height: 100vh;
      background: var(--primary-background-color, #fafafa);
      color: var(--primary-text-color, #212121);
      font-family: var(--ha-font-family-body, Roboto, system-ui, sans-serif);
      --radius: var(--ha-card-border-radius, 12px);
      --line: var(--divider-color, rgba(0, 0, 0, 0.12));
      --muted: var(--secondary-text-color, #727272);
      --surface: var(--card-background-color, #fff);
      --accent: var(--primary-color, #03a9f4);
    }
    .toolbar {
      display: flex;
      align-items: center;
      gap: 8px;
      height: var(--header-height, 56px);
      padding: 0 16px;
      background: var(--app-header-background-color, var(--primary-color, #03a9f4));
      color: var(--app-header-text-color, #fff);
      position: sticky;
      top: 0;
      z-index: 3;
    }
    .toolbar .title {
      font-size: 20px;
      font-weight: 400;
    }
    .icon {
      background: none;
      border: none;
      color: inherit;
      padding: 8px;
      margin-left: -8px;
      cursor: pointer;
    }
    .icon svg {
      width: 24px;
      height: 24px;
      fill: currentColor;
    }
    .content {
      max-width: 1100px;
      margin: 0 auto;
      padding: 16px 16px 24px;
    }
    .header {
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      margin-bottom: 12px;
    }
    .project {
      font-size: 22px;
    }
    .sub {
      color: var(--muted);
      font-size: 13px;
    }
    .actions {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    button,
    .button {
      font: inherit;
      font-size: 14px;
      font-weight: 500;
      border-radius: 18px;
      padding: 7px 16px;
      border: 1px solid var(--line);
      background: var(--surface);
      color: var(--accent);
      cursor: pointer;
      display: inline-flex;
      align-items: center;
    }
    button:disabled,
    .button.disabled {
      opacity: 0.5;
      cursor: default;
    }
    button.primary {
      background: var(--accent);
      color: var(--text-primary-color, #fff);
      border-color: var(--accent);
    }
    button.text {
      border-color: transparent;
      background: none;
    }
    .alert {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 8px;
      padding: 10px 14px;
      border-radius: var(--radius);
      margin-bottom: 12px;
      background: var(--surface);
      border-left: 4px solid var(--accent);
    }
    .alert.error {
      border-color: var(--error-color, #db4437);
    }
    .alert.warn {
      border-color: var(--warning-color, #ffa600);
    }
    .alert span {
      flex: 1 1 240px;
    }
    input[type="text"],
    input[type="search"],
    input[type="password"],
    select {
      font: inherit;
      font-size: 14px;
      color: var(--primary-text-color);
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 7px 10px;
      min-width: 0;
    }
    input:focus-visible,
    select:focus-visible,
    button:focus-visible {
      outline: 2px solid var(--accent);
      outline-offset: 1px;
    }
    .filters {
      display: flex;
      gap: 8px;
      margin-bottom: 8px;
    }
    .search {
      flex: 1;
    }
    .chips {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-bottom: 16px;
    }
    .chip {
      color: var(--primary-text-color);
      padding: 4px 12px;
      font-weight: 400;
    }
    .chip.active {
      background: var(--accent);
      border-color: var(--accent);
      color: var(--text-primary-color, #fff);
    }
    .chip.accent:not(.active) {
      border-color: var(--accent);
    }
    .chip .n {
      color: inherit;
      opacity: 0.7;
      margin-left: 4px;
    }
    .group {
      background: var(--surface);
      border-radius: var(--radius);
      box-shadow: var(--ha-card-box-shadow, none);
      border: 1px solid var(--ha-card-border-color, var(--line));
      margin-bottom: 16px;
      overflow: hidden;
    }
    .group-head {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 10px 16px;
      border-bottom: 1px solid var(--line);
    }
    .group-head h2 {
      font-size: 16px;
      font-weight: 500;
      margin: 0;
      flex: 1;
    }
    .n {
      color: var(--muted);
      font-size: 13px;
    }
    .row {
      display: grid;
      grid-template-columns: auto minmax(0, 1fr) 150px 150px;
      gap: 12px;
      align-items: center;
      padding: 8px 16px;
      border-bottom: 1px solid var(--line);
    }
    .rows > .row:last-child {
      border-bottom: none;
    }
    .row.off .name,
    .row.off .meta {
      opacity: 0.6;
    }
    .row.unmapped {
      grid-template-columns: 80px minmax(0, 1fr) auto;
    }
    .check {
      width: 18px;
      height: 18px;
      accent-color: var(--accent);
    }
    .main {
      min-width: 0;
    }
    input.name {
      width: 100%;
      box-sizing: border-box;
      border-color: transparent;
      border-bottom: 1px dashed var(--line);
      border-radius: 4px 4px 0 0;
      background: transparent;
      padding: 4px 6px;
      margin-left: -6px;
    }
    input.name:hover,
    input.name:focus {
      border-color: var(--line);
      background: var(--surface);
    }
    input.name::placeholder {
      color: var(--primary-text-color);
      opacity: 1;
    }
    .meta {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      font-size: 12px;
      color: var(--muted);
      margin-top: 2px;
    }
    .meta a {
      color: var(--accent);
      text-decoration: none;
    }
    code {
      font-family: var(--ha-font-family-code, ui-monospace, monospace);
      font-size: 12px;
      background: var(--secondary-background-color, rgba(0, 0, 0, 0.05));
      border-radius: 4px;
      padding: 1px 5px;
    }
    .type {
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      gap: 4px;
    }
    .type select {
      width: 100%;
    }
    .domain {
      font-size: 14px;
    }
    .hint {
      font-size: 12px;
      padding: 2px 10px;
      border-style: dashed;
    }
    .status {
      text-align: right;
      min-width: 0;
    }
    .badge {
      display: inline-block;
      font-size: 12px;
      border-radius: 10px;
      padding: 2px 10px;
      background: var(--secondary-background-color, rgba(0, 0, 0, 0.06));
      color: var(--primary-text-color);
      white-space: nowrap;
    }
    .badge.new,
    .badge.pending {
      background: var(--accent);
      color: var(--text-primary-color, #fff);
    }
    .badge.changed {
      background: var(--warning-color, #ffa600);
      color: #000;
    }
    .badge.unchanged {
      background: var(--success-color, #43a047);
      color: #fff;
    }
    .badge.removed,
    .badge.invalid {
      background: var(--error-color, #db4437);
      color: #fff;
    }
    .reason {
      font-size: 12px;
      color: var(--muted);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      margin-top: 2px;
    }
    .badge.adopt {
      background: var(--accent);
      color: var(--text-primary-color, #fff);
    }
    .badge.existing {
      background: var(--secondary-background-color, rgba(0, 0, 0, 0.06));
    }
    button.link {
      border: none;
      background: none;
      padding: 2px 0;
      margin-top: 4px;
      font-size: 12px;
      font-weight: 500;
      border-radius: 4px;
    }
    /* "already exists" only on hover/focus, it is rarely needed */
    @media (hover: hover) {
      .row .mark {
        opacity: 0;
      }
      .row:hover .mark,
      .row:focus-within .mark {
        opacity: 1;
      }
    }
    .conflict-box {
      grid-column: 2 / -1;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 8px 12px;
      font-size: 13px;
      padding: 8px 12px;
      border-radius: 8px;
      background: var(--secondary-background-color, rgba(0, 0, 0, 0.04));
    }
    .conflict-box span:first-child {
      flex: 1 1 260px;
    }
    .conflict-box button {
      padding: 4px 12px;
      font-size: 13px;
    }
    .empty {
      padding: 48px 16px;
      text-align: center;
      color: var(--muted);
    }
    .bar {
      position: sticky;
      bottom: 0;
      background: var(--surface);
      border-top: 1px solid var(--line);
      box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.12);
      z-index: 4;
    }
    .bar-main {
      max-width: 1100px;
      margin: 0 auto;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 8px;
      padding: 10px 16px;
    }
    .bar-info {
      flex: 1 1 auto;
      min-width: 0;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      column-gap: 12px;
    }
    .bar .summary {
      color: var(--primary-text-color);
      padding-left: 0;
    }
    .bar-actions {
      display: flex;
      gap: 8px;
      margin-left: auto;
    }
    .changes {
      max-width: 1100px;
      margin: 0 auto;
      max-height: 40vh;
      overflow: auto;
      padding: 12px 16px 0;
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 12px;
      font-size: 14px;
    }
    .changes ul {
      margin: 4px 0 0;
      padding-left: 18px;
    }
    @media (max-width: 700px) {
      .row {
        grid-template-columns: auto minmax(0, 1fr) auto;
        grid-template-areas: "check main main" ". type status";
        row-gap: 6px;
      }
      .check {
        grid-area: check;
      }
      .main {
        grid-area: main;
      }
      .type {
        grid-area: type;
        flex-direction: row;
        align-items: center;
      }
      .type select {
        width: auto;
      }
      .status {
        grid-area: status;
      }
      .conflict-box {
        grid-column: 1 / -1;
      }
    }
  `;
}

customElements.define("knx-project-sync-panel", KnxProjectSyncPanel);
