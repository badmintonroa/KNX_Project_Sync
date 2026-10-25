/** Texts of the panel (German and English). */
type Filter = "all" | "active" | "pending" | "off" | "issues" | "gone" | "unmapped";

export interface Strings {
  menu: string;
  loading: string;
  noProject: string;
  lastImport: (time: string) => string;
  neverImported: string;
  count: (n: number) => string;
  fromKnx: string;
  upload: string;
  staged: string;
  discardProject: string;
  loaded: string;
  passwordNeeded: string;
  password: string;
  open: string;
  cancel: string;
  search: string;
  groupBy: string;
  byRoom: string;
  byType: string;
  noRoom: string;
  nothingFound: string;
  selectGroup: (name: string) => string;
  create: (name: string) => string;
  name: string;
  type: string;
  suggestLight: string;
  suggestLightTitle: string;
  unmappedHint: string;
  willAdd: string;
  willChange: string;
  willRemove: string;
  summary: (added: number, changed: number, removed: number) => string;
  stillPending: (n: number) => string;
  discard: string;
  apply: string;
  applying: string;
  applied: (summary: Record<string, number>) => string;
  filters: Record<Filter, string>;
  status: Record<string, string>;
  reasons: Record<string, string>;
  domains: Record<string, string>;
  errors: Record<string, string>;
}

const de: Strings = {
  menu: "Menü",
  loading: "Lade …",
  noProject: "Noch kein Projekt importiert. Lade eine .knxproj-Datei hoch oder lies das Projekt aus dem KNX-Panel ein.",
  lastImport: (time) => `Letzter Import: ${time}`,
  neverImported: "Noch nicht importiert",
  count: (n) => `${n} Entities angelegt`,
  fromKnx: "Aus KNX-Panel einlesen",
  upload: "Projektdatei hochladen",
  staged: "Neue Projektversion geladen. Prüfe die Änderungen und übernimm sie, oder verwirf sie.",
  discardProject: "Projektversion verwerfen",
  loaded: "Projekt eingelesen. Neue Entities sind unter „Neu verfügbar“ zu finden.",
  passwordNeeded: "Das Projekt ist passwortgeschützt.",
  password: "Projekt-Passwort",
  open: "Öffnen",
  cancel: "Abbrechen",
  search: "Suchen nach Name, Adresse, Raum …",
  groupBy: "Gruppieren",
  byRoom: "Nach Raum",
  byType: "Nach Typ",
  noRoom: "Ohne Raum",
  nothingFound: "Keine Entities für diesen Filter.",
  selectGroup: (name) => `Alle in ${name} auswählen`,
  create: (name) => `${name} anlegen`,
  name: "Name",
  type: "Typ",
  suggestLight: "💡 Als Licht?",
  suggestLightTitle: "Der Name deutet auf eine Lampe hin. Als Licht anlegen.",
  unmappedHint:
    "Für diese Gruppenadressen wurde kein Entity-Typ erkannt. Sie werden nicht angelegt. Lege sie bei Bedarf von Hand in der KNX-YAML oder im KNX-Panel an.",
  willAdd: "Wird hinzugefügt",
  willChange: "Wird geändert",
  willRemove: "Wird entfernt",
  summary: (a, c, r) => `+${a} hinzufügen · ${c} ändern · −${r} entfernen`,
  stillPending: (n) => `${n} neu verfügbar, nicht ausgewählt`,
  discard: "Verwerfen",
  apply: "Übernehmen",
  applying: "Übernehme …",
  applied: (s) =>
    `Übernommen: ${s.new ?? 0} neu, ${s.changed ?? 0} geändert, ${s.deleted ?? 0} entfernt. KNX wurde neu geladen.`,
  filters: {
    all: "Alle",
    active: "Angelegt",
    pending: "Neu verfügbar",
    off: "Abgewählt",
    issues: "Nicht möglich",
    gone: "Nicht mehr im Projekt",
    unmapped: "Ohne Typ",
  },
  status: {
    new: "Wird hinzugefügt",
    changed: "Wird geändert",
    retyped: "Typ wird geändert",
    unchanged: "Aktiv",
    kept: "Behalten",
    removed: "Wird entfernt",
    pending: "Neu verfügbar",
    deselected: "Abgewählt",
    deselected_removed: "Wird entfernt",
    excluded: "Typ ausgeschlossen",
    duplicate: "Doppelt",
    invalid: "Ungültig",
    conflict: "Eigene YAML",
  },
  reasons: {
    own_yaml: "Schon in deiner eigenen KNX-YAML definiert",
    light: "GA schon von einem Licht belegt",
    unique_id: "Gleiche Gruppenadresse wie eine andere Entity",
  },
  domains: {
    switch: "Schalter",
    light: "Licht",
    binary_sensor: "Binärsensor",
    sensor: "Sensor",
    time: "Uhrzeit",
    date: "Datum",
    datetime: "Datum/Uhrzeit",
    cover: "Rollladen/Jalousie",
    scene: "Szene",
    climate: "Klima",
    weather: "Wetter",
  },
  errors: {
    invalid_password: "Falsches oder fehlendes Projekt-Passwort.",
    invalid_project: "Keine lesbare ETS-Projektdatei.",
    no_knx_project: "Im KNX-Panel ist kein Projekt hochgeladen.",
    not_set_up: "KNX Project Sync ist nicht eingerichtet.",
    no_project: "Es wurde noch kein Projekt importiert.",
  },
};

const en: Strings = {
  menu: "Menu",
  loading: "Loading …",
  noProject: "No project imported yet. Upload a .knxproj file or read the project from the KNX panel.",
  lastImport: (time) => `Last import: ${time}`,
  neverImported: "Not imported yet",
  count: (n) => `${n} entities created`,
  fromKnx: "Read from KNX panel",
  upload: "Upload project file",
  staged: "New project version loaded. Review the changes and apply them, or discard them.",
  discardProject: "Discard project version",
  loaded: "Project loaded. New entities are listed under “Newly available”.",
  passwordNeeded: "The project is password protected.",
  password: "Project password",
  open: "Open",
  cancel: "Cancel",
  search: "Search name, address, room …",
  groupBy: "Group by",
  byRoom: "By room",
  byType: "By type",
  noRoom: "No room",
  nothingFound: "No entities for this filter.",
  selectGroup: (name) => `Select all in ${name}`,
  create: (name) => `Create ${name}`,
  name: "Name",
  type: "Type",
  suggestLight: "💡 A light?",
  suggestLightTitle: "The name suggests a lamp. Create it as a light.",
  unmappedHint:
    "No entity type was detected for these group addresses, so they are not created. Add them by hand in the KNX YAML or the KNX panel if needed.",
  willAdd: "Will be added",
  willChange: "Will be changed",
  willRemove: "Will be removed",
  summary: (a, c, r) => `+${a} add · ${c} change · −${r} remove`,
  stillPending: (n) => `${n} newly available, not selected`,
  discard: "Discard",
  apply: "Apply",
  applying: "Applying …",
  applied: (s) => `Applied: ${s.new ?? 0} new, ${s.changed ?? 0} changed, ${s.deleted ?? 0} removed. KNX was reloaded.`,
  filters: {
    all: "All",
    active: "Created",
    pending: "Newly available",
    off: "Deselected",
    issues: "Not possible",
    gone: "No longer in project",
    unmapped: "No type",
  },
  status: {
    new: "Will be added",
    changed: "Will change",
    retyped: "Type changes",
    unchanged: "Active",
    kept: "Kept",
    removed: "Will be removed",
    pending: "Newly available",
    deselected: "Deselected",
    deselected_removed: "Will be removed",
    excluded: "Type excluded",
    duplicate: "Duplicate",
    invalid: "Invalid",
    conflict: "Own YAML",
  },
  reasons: {
    own_yaml: "Already defined in your own KNX YAML",
    light: "GA already used by a light",
    unique_id: "Same group address as another entity",
  },
  domains: {
    switch: "Switch",
    light: "Light",
    binary_sensor: "Binary sensor",
    sensor: "Sensor",
    time: "Time",
    date: "Date",
    datetime: "Date/time",
    cover: "Cover",
    scene: "Scene",
    climate: "Climate",
    weather: "Weather",
  },
  errors: {
    invalid_password: "Wrong or missing project password.",
    invalid_project: "Not a readable ETS project file.",
    no_knx_project: "No project is uploaded in the KNX panel.",
    not_set_up: "KNX Project Sync is not set up.",
    no_project: "No project has been imported yet.",
  },
};

export const STRINGS: Record<string, Strings> = { de, en };
