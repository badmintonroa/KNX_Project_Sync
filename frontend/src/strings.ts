/** Texts of the panel (German and English). */
type Filter = "all" | "active" | "pending" | "off" | "existing" | "issues" | "gone" | "unmapped";

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
  willAdopt: string;
  adoptCount: (n: number) => string;
  adopt: string;
  undo: string;
  ownYaml: string;
  conflictInfo: (domain: string, name: string, where: string) => string;
  adoptInfo: (where: string) => string;
  notAdoptable: string;
  markExisting: string;
  existingTitle: string;
  resetConfig: string;
  ownConfigTitle: string;
  adoptFailed: (reason: string) => string;
  adoptReasons: Record<string, string>;
  editAddresses: string;
  doneAddresses: string;
  addAddress: string;
  removeAddress: (field: string) => string;
  fromEts: string;
  etsValue: (address: string) => string;
  addedByHand: string;
  reset: string;
  invalidAddress: string;
  fixAddresses: string;
  fieldLabel: (field: string) => string;
  eyebrow: string;
  sources: Record<string, string>;
  lastImportLine: (time: string, source: string) => string;
  stagedTitle: string;
  stagedDetail: (pending: number, changed: number, removed: number) => string;
  discardVersion: string;
  stats: Record<"active" | "pending" | "off" | "unmapped", [string, string]>;
  moreFilters: string;
  roomCount: (on: number, total: number) => string;
  allOn: string;
  allOff: string;
  barCounts: Record<"add" | "change" | "remove" | "adopt", string>;
  showDetails: string;
  hideDetails: string;
  applyLong: string;
  filters: Record<Filter, string>;
  status: Record<string, string>;
  reasons: Record<string, string>;
  domains: Record<string, string>;
  errors: Record<string, string>;
}

const FIELDS_DE: Record<string, string> = {
  "address": "Schalten / Senden",
  "state_address": "Status",
  "brightness_address": "Helligkeit",
  "brightness_state_address": "Helligkeit Status",
  "color_temperature_address": "Farbtemperatur",
  "color_temperature_state_address": "Farbtemperatur Status",
  "color_address": "Farbe",
  "color_state_address": "Farbe Status",
  "move_long_address": "Auf/Ab",
  "move_short_address": "Schritt/Stopp",
  "stop_address": "Stopp",
  "position_address": "Position",
  "position_state_address": "Position Status",
  "angle_address": "Lamelle",
  "angle_state_address": "Lamelle Status",
  "temperature_address": "Ist-Temperatur",
  "target_temperature_address": "Soll-Temperatur",
  "target_temperature_state_address": "Soll-Temperatur Status",
  "setpoint_shift_address": "Sollwertverschiebung",
  "setpoint_shift_state_address": "Sollwertverschiebung Status",
  "operation_mode_address": "Betriebsart",
  "operation_mode_state_address": "Betriebsart Status",
  "on_off_address": "Ein/Aus",
  "on_off_state_address": "Ein/Aus Status",
  "address_temperature": "Temperatur",
  "address_brightness_south": "Helligkeit Süd",
  "address_brightness_east": "Helligkeit Ost",
  "address_brightness_west": "Helligkeit West",
  "address_brightness_north": "Helligkeit Nord",
  "address_wind_speed": "Windgeschwindigkeit",
  "address_rain_alarm": "Regenalarm",
  "address_frost_alarm": "Frostalarm",
  "address_wind_alarm": "Windalarm",
  "address_day_night": "Tag/Nacht",
  "address_air_pressure": "Luftdruck",
  "address_humidity": "Luftfeuchte"
};
const FIELDS_EN: Record<string, string> = {
  "address": "Switch / send",
  "state_address": "State",
  "brightness_address": "Brightness",
  "brightness_state_address": "Brightness state",
  "color_temperature_address": "Color temperature",
  "color_temperature_state_address": "Color temperature state",
  "color_address": "Color",
  "color_state_address": "Color state",
  "move_long_address": "Up/down",
  "move_short_address": "Step/stop",
  "stop_address": "Stop",
  "position_address": "Position",
  "position_state_address": "Position state",
  "angle_address": "Slat angle",
  "angle_state_address": "Slat angle state",
  "temperature_address": "Current temperature",
  "target_temperature_address": "Target temperature",
  "target_temperature_state_address": "Target temperature state",
  "setpoint_shift_address": "Setpoint shift",
  "setpoint_shift_state_address": "Setpoint shift state",
  "operation_mode_address": "Operation mode",
  "operation_mode_state_address": "Operation mode state",
  "on_off_address": "On/off",
  "on_off_state_address": "On/off state",
  "address_temperature": "Temperature",
  "address_brightness_south": "Brightness south",
  "address_brightness_east": "Brightness east",
  "address_brightness_west": "Brightness west",
  "address_brightness_north": "Brightness north",
  "address_wind_speed": "Wind speed",
  "address_rain_alarm": "Rain alarm",
  "address_frost_alarm": "Frost alarm",
  "address_wind_alarm": "Wind alarm",
  "address_day_night": "Day/night",
  "address_air_pressure": "Air pressure",
  "address_humidity": "Humidity"
};

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
  suggestLight: "Klingt nach Licht",
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
  willAdopt: "Wird aus deiner YAML übernommen",
  adoptCount: (n) => `${n} übernehmen`,
  adopt: "In App übernehmen",
  undo: "Rückgängig",
  ownYaml: "deiner eigenen KNX-YAML",
  conflictInfo: (domain, name, where) => `Schon in deiner YAML: ${domain} „${name}“ (${where}). Wird nicht doppelt angelegt.`,
  adoptInfo: (where) =>
    `Wird mit deiner Konfiguration in die App übernommen und aus ${where} entfernt. Vorher wird eine Sicherung angelegt.`,
  notAdoptable: "Nicht automatisch übernehmbar, bitte in der YAML entfernen.",
  markExisting: "Schon vorhanden",
  existingTitle: "Diese Entity gibt es schon (z. B. in deiner YAML als anderer Typ). Nicht anlegen.",
  resetConfig: "Auf Projekt zurücksetzen",
  ownConfigTitle: "Nutzt deine übernommene Konfiguration. Zurücksetzen auf die Erkennung aus dem ETS-Projekt.",
  adoptFailed: (reason) => `Übernahme aus deiner YAML nicht möglich: ${reason}. Es wurde nichts geändert.`,
  adoptReasons: {
    not_a_list_item: "der Eintrag ist kein einfacher Listeneintrag („- name: …“)",
    flow_style: "der Eintrag steht in Kurzschreibweise ({ … })",
    outside_config: "die Datei liegt außerhalb des Konfigurationsordners",
    line_not_found: "die Datei hat sich geändert, bitte neu laden",
    verification: "nach dem Entfernen hätte sich mehr als dieser Eintrag geändert",
  },
  editAddresses: "Adressen bearbeiten",
  doneAddresses: "Fertig",
  addAddress: "Adresse hinzufügen …",
  removeAddress: (field) => `${field} entfernen`,
  fromEts: "aus der ETS",
  etsValue: (a) => `ETS: ${a ? a : "keine"} · `,
  addedByHand: "von Hand hinzugefügt",
  reset: "zurücksetzen",
  invalidAddress: "Keine gültige Gruppenadresse (z. B. 1/2/3)",
  fixAddresses: "Ungültige Gruppenadresse korrigieren",
  fieldLabel: (f) => FIELDS_DE[f] ?? f,
  eyebrow: "ETS-Projekt",
  sources: { upload: "Datei-Upload", knx_project: "KNX-Panel", file: "Datei" },
  lastImportLine: (time, source) => `Letzter Import ${time} · Quelle: ${source}`,
  stagedTitle: "Neue Projektversion geladen",
  stagedDetail: (p, c, r) =>
    `${p} neue ${p === 1 ? "Entity" : "Entities"} gefunden, ${c} geändert, ${r} nicht mehr im Projekt. Noch nichts übernommen.`,
  discardVersion: "Version verwerfen",
  stats: {
    active: ["Angelegt", "Entities"],
    pending: ["Neu verfügbar", "zum Hinzufügen"],
    off: ["Abgewählt", "nicht angelegt"],
    unmapped: ["Ohne Typ", "Gruppenadressen"],
  },
  moreFilters: "Weitere",
  roomCount: (on, total) => `${on} von ${total} angelegt`,
  allOn: "Alle anlegen",
  allOff: "Alle abwählen",
  barCounts: { add: "hinzufügen", change: "ändern", remove: "entfernen", adopt: "übernehmen" },
  showDetails: "Details anzeigen",
  hideDetails: "Details ausblenden",
  applyLong: "Übernehmen und KNX neu laden",
  filters: {
    all: "Alle",
    active: "Angelegt",
    pending: "Neu verfügbar",
    off: "Abgewählt",
    existing: "Schon vorhanden",
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
    existing: "Schon vorhanden",
    adopt: "Wird übernommen",
    own_config: "Aktiv · eigene Konfiguration",
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
  suggestLight: "Sounds like a light",
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
  willAdopt: "Taken over from your YAML",
  adoptCount: (n) => `${n} take over`,
  adopt: "Take over into the app",
  undo: "Undo",
  ownYaml: "your own KNX YAML",
  conflictInfo: (domain, name, where) => `Already in your YAML: ${domain} “${name}” (${where}). Not created twice.`,
  adoptInfo: (where) => `Taken over into the app with your configuration and removed from ${where}. A backup is made first.`,
  notAdoptable: "Cannot be taken over automatically, please remove it from the YAML.",
  markExisting: "Already exists",
  existingTitle: "This entity already exists (e.g. in your YAML as another type). Do not create it.",
  resetConfig: "Reset to project",
  ownConfigTitle: "Uses your taken-over configuration. Reset to what the ETS project detects.",
  adoptFailed: (reason) => `Could not take over from your YAML: ${reason}. Nothing was changed.`,
  adoptReasons: {
    not_a_list_item: "the entry is not a plain list item (“- name: …”)",
    flow_style: "the entry uses the short flow style ({ … })",
    outside_config: "the file is outside the configuration folder",
    line_not_found: "the file has changed, please reload",
    verification: "removing it would have changed more than this entry",
  },
  editAddresses: "Edit addresses",
  doneAddresses: "Done",
  addAddress: "Add address …",
  removeAddress: (field) => `Remove ${field}`,
  fromEts: "from ETS",
  etsValue: (a) => `ETS: ${a ? a : "none"} · `,
  addedByHand: "added by hand",
  reset: "reset",
  invalidAddress: "Not a valid group address (e.g. 1/2/3)",
  fixAddresses: "Fix the invalid group address",
  fieldLabel: (f) => FIELDS_EN[f] ?? f,
  eyebrow: "ETS project",
  sources: { upload: "file upload", knx_project: "KNX panel", file: "file" },
  lastImportLine: (time, source) => `Last import ${time} · Source: ${source}`,
  stagedTitle: "New project version loaded",
  stagedDetail: (p, c, r) =>
    `${p} new ${p === 1 ? "entity" : "entities"} found, ${c} changed, ${r} no longer in the project. Nothing applied yet.`,
  discardVersion: "Discard version",
  stats: {
    active: ["Created", "entities"],
    pending: ["Newly available", "to add"],
    off: ["Deselected", "not created"],
    unmapped: ["No type", "group addresses"],
  },
  moreFilters: "More",
  roomCount: (on, total) => `${on} of ${total} created`,
  allOn: "Create all",
  allOff: "Deselect all",
  barCounts: { add: "add", change: "change", remove: "remove", adopt: "take over" },
  showDetails: "Show details",
  hideDetails: "Hide details",
  applyLong: "Apply and reload KNX",
  filters: {
    all: "All",
    active: "Created",
    pending: "Newly available",
    off: "Deselected",
    existing: "Already exists",
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
    existing: "Already exists",
    adopt: "Will be taken over",
    own_config: "Active · own configuration",
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
