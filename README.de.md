# KNX Project Sync

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/docs/faq/custom_repositories)
[![Release](https://img.shields.io/github/v/release/badmintonroa/KNX_Project_Sync?include_prereleases)](https://github.com/badmintonroa/KNX_Project_Sync/releases)
[![Tests](https://github.com/badmintonroa/KNX_Project_Sync/actions/workflows/tests.yaml/badge.svg)](https://github.com/badmintonroa/KNX_Project_Sync/actions/workflows/tests.yaml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

🇬🇧 [English version](README.md)

Legt die KNX-Entities in Home Assistant aus deiner ETS-Projektdatei (`.knxproj`) an und hält sie aktuell, wenn sich das Projekt ändert. In einem Panel wählst du die Entities aus, benennst sie um und korrigierst sie, bevor etwas angelegt wird. Updates behalten entity_ids, Namen, Bereiche und den Verlauf.

[![In HACS öffnen](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=badmintonroa&repository=KNX_Project_Sync&category=integration)
[![Integration hinzufügen](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=knx_project_sync)

![Das Panel von KNX Project Sync](https://raw.githubusercontent.com/badmintonroa/KNX_Project_Sync/main/docs/images/panel-de.png)

> [!NOTE]
> Sichere deine Konfiguration vor dem ersten Import. Die Änderungen stehen im [Changelog](CHANGELOG.md).

## Inhalt

- [Funktionen](#funktionen)
- [Installation](#installation)
- [Was die Integration anlegt](#was-die-integration-anlegt)
- [Unterstützte Entities](#unterstützte-entities)
- [Wie die Entities erkannt werden](#wie-die-entities-erkannt-werden)
- [Projekt aktualisieren](#projekt-aktualisieren)
- [Automatisierung](#automatisierung)
- [Deinstallation](#deinstallation)
- [Fehlerbehebung](#fehlerbehebung)
- [Mithelfen](#mithelfen)

## Funktionen

- Liest Projekte aus ETS 4, 5 und 6, auch passwortgeschützte. Dafür wird [xknxproject](https://github.com/XKNX/xknxproject) verwendet, dieselbe Bibliothek wie in der offiziellen KNX-Integration. Alternativ wird das Projekt genutzt, das du schon im KNX-Panel hochgeladen hast.
- Erkennt Lichter, Schalter, Jalousien, Klima, Wetterstationen, Sensoren, Texte, Szenen und mehr (siehe [Unterstützte Entities](#unterstützte-entities)).
- **Panel in der Seitenleiste:** Entities auswählen, umbenennen, falsche Gruppenadressen korrigieren, Typ umstellen (Schalter ↔ Licht, Text ↔ Sensor). Es ändert sich nichts, bis du auf *Übernehmen* klickst.
- **Deine eigene KNX-YAML wird beachtet:** Was du schon von Hand angelegt hast, wird erkannt und nicht doppelt angelegt. Du kannst es in die App übernehmen.
- **Updates ohne Verluste:** entity_ids, Namen, Bereiche, Dashboards und Verlauf bleiben erhalten, auch wenn eine Gruppenadresse in der ETS umadressiert wird. Neue Entities werden nur vorgeschlagen und nie von selbst angelegt.
- ETS-Räume werden zu Bereichen in Home Assistant.
- Alles läuft lokal. Das Projektpasswort wird nur zum Öffnen der Datei verwendet und nicht gespeichert.

Die Erkennung ist ein Python-Port von [knx2home](https://github.com/badmintonroa/knx2home). Tests prüfen, dass beide genau dasselbe Ergebnis liefern.

## Installation

### Voraussetzungen

- Home Assistant 2025.4 oder neuer
- Die [KNX-Integration](https://www.home-assistant.io/integrations/knx/), eingerichtet und verbunden
- [HACS](https://hacs.xyz)
- Dein ETS-Projekt als `.knxproj` exportiert

### 1. Installieren

**Mit HACS (empfohlen)**

1. Oben auf *In HACS öffnen* klicken, oder in HACS → ⋮ → *Benutzerdefinierte Repositories* die Adresse `https://github.com/badmintonroa/KNX_Project_Sync` mit Typ *Integration* hinzufügen.
2. Herunterladen und Home Assistant neu starten.

**Manuell**

`custom_components/knx_project_sync` aus dem [aktuellen Release](https://github.com/badmintonroa/KNX_Project_Sync/releases) nach `config/custom_components/` kopieren und Home Assistant neu starten.

### 2. Einrichten

1. *Einstellungen → Geräte & Dienste → Integration hinzufügen → KNX Project Sync* (oder oben auf *Integration hinzufügen* klicken).
2. Quelle wählen: eine `.knxproj`-Datei hochladen oder das Projekt aus dem KNX-Panel verwenden.
3. Das Projekt wird eingelesen und du landest im Panel. **Angelegt ist noch nichts.**

### 3. Erster Import

1. Im Panel **KNX Project Sync** (Seitenleiste, nur für Admins) sind alle erkannten Entities ausgewählt.
2. Abwählen, was du nicht willst, Entities umbenennen, Gruppenadressen korrigieren oder Typen ändern.
3. Auf **Übernehmen** klicken. Die Entities werden geschrieben und die KNX-Integration wird neu geladen. Ein Neustart ist nicht nötig.

### Die Paket-Zeile

Die Entities stehen in einer eigenen Datei. So bleiben deine `configuration.yaml` und deine eigene KNX-Konfiguration unangetastet. Home Assistant liest so eine Datei aber nur über [Pakete](https://www.home-assistant.io/docs/configuration/packages/):

```yaml
homeassistant:
  packages: !include_dir_named packages
```

Fehlt diese Zeile, zeigen das Panel eine Karte und Home Assistant eine Reparatur, beide mit einem Knopf, der sie einträgt. Die `configuration.yaml` wird vorher gesichert. Das Ergebnis wird mit dem YAML-Loader von Home Assistant geprüft, und bei einem Fehler wird die Sicherung zurückgespielt. Lädst du schon Pakete aus einem anderen Ordner, wird stattdessen die Datei dorthin verschoben, und die `configuration.yaml` bleibt, wie sie ist.

## Was die Integration anlegt

```
config/
├── configuration.yaml                                  eine Zeile, nur auf deinen Klick
├── configuration.yaml.knx_project_sync-<zeit>.bak      Sicherung vor dieser Änderung
├── packages/
│   └── knx_project_sync.yaml                           alle erzeugten Entities
├── <deine KNX-YAML>.knx_project_sync-<zeit>.bak        Sicherung, wenn du Entities übernimmst
└── .storage/
    └── knx_project_sync                                Auswahl, Namen, Korrekturen, letzter Import
```

| Datei | Inhalt | Von Hand ändern? |
|---|---|---|
| `packages/knx_project_sync.yaml` | Die `knx:`-Konfiguration aller ausgewählten Entities. Wird bei jedem *Übernehmen* neu geschrieben. Der Pfad lässt sich in den Einstellungen ändern. | Nein. Nutze das Panel, deine Änderungen würden überschrieben. |
| `.storage/knx_project_sync` | Das eingelesene Projekt, deine Auswahl im Panel und was zuletzt übernommen wurde. | Nein |
| `*.knx_project_sync-*.bak` | Sicherungen, bevor die Integration eine deiner Dateien ändert. | Löschen, wenn du sie nicht mehr brauchst. |

So sieht die Paket-Datei aus:

```yaml
# Automatisch erzeugt von knx_project_sync – nicht von Hand bearbeiten.
# Generated by knx_project_sync – do not edit, changes are overwritten on the next import.
# Projekt / project: Musterhaus
knx:
  light:
    - name: Wohnzimmer Decke
      address: 1/1/10
      state_address: 1/5/10
      brightness_address: 1/3/10
      brightness_state_address: 1/4/10
  sensor:
    - name: Wohnzimmer Temperatur
      state_address: 3/0/1
      type: temperature
```

In Home Assistant kommen dazu:

- das Panel **KNX Project Sync** in der Seitenleiste
- ein Sensor **Letzter Import** (Zeitstempel; Projekt, Quelle und die Zahlen des letzten Imports als Attribute)
- **Bereiche** mit den Namen der ETS-Räume, für Entities ohne Bereich (abschaltbar)
- Benachrichtigungen, wenn eine neue Projektversion neue Entities bringt
- [Diagnosedaten](https://www.home-assistant.io/docs/configuration/troubleshooting/#download-diagnostics) für Fehlermeldungen

Die Entities selbst gehören zur KNX-Integration. Es sind normale KNX-Entities, so als hättest du die YAML selbst geschrieben.

### Einstellungen

*Einstellungen → Geräte & Dienste → KNX Project Sync → Konfigurieren → Einstellungen*

| Option | Standard | Bedeutung |
|---|---|---|
| Entity-Typen | alle | Nur diese Typen werden angelegt. |
| Entities, die im Projekt fehlen | löschen | *Löschen* entfernt sie, *Behalten* lässt sie stehen. |
| Bereiche aus ETS-Räumen zuweisen | an | Nur für Entities ohne Bereich. Bereiche, die du gesetzt hast, werden nie geändert. |
| Paket-Datei | `packages/knx_project_sync.yaml` | Wohin die Entities geschrieben werden. |

## Unterstützte Entities

| Typ | Erkannt über | Felder |
|---|---|---|
| Licht | Kanäle von Dimmaktoren, ETS-6-Funktionen, Adressmuster, Namensmuster (siehe unten) | Schalten, Status, Helligkeit, Helligkeit-Status |
| Schalter | DPT 1.001 (auch 1.002, 2.001) | Adresse, Status-Adresse |
| Binärsensor | DPT 1.001 mit *Status* im Namen, 1.005, 1.006, 1.009 | Status-Adresse |
| Sensor | DPT 5.001, 7.xxx, 8.xxx, 9.xxx, 12.xxx, 20.102, 20.105 oder Namen wie *Temperatur*, *Feuchte*, *CO2*, *Lux* | Status-Adresse, Typ |
| Text | DPT 16.000, 16.001 | Adresse, Status-Adresse |
| Zeit / Datum / Datum und Zeit | DPT 10.001 / 11.001 / 19.001 | Adresse |
| Jalousie | Kanäle von Jalousieaktoren, oder DPT 1.007, 1.008, 1.010, 5.001, 5.003 mit Jalousie-Namen (*Jalousie*, *Rollo*, *blind*, …) | Auf/Ab, Schritt, Stopp, Position, Lamelle, jeweils mit Status |
| Klima | Kanal eines Aktors oder Raumreglers mit Ist- und Solltemperatur (9.001) | Sollwertverschiebung, Betriebsart, Reglermodus, Heizen/Kühlen, Stellwert, Feuchte |
| Wetter | Wetterstation mit Außentemperatur und Wind oder Helligkeit | Temperatur, Helligkeit N/O/S/W, Windgeschwindigkeit und -richtung, Regen-/Frost-/Windalarm, Tag/Nacht, Luftdruck, Feuchte |
| Szene | DPT 17.001, 18.001, Namen mit *Szene* | Adresse, Szenennummer |

Noch nicht unterstützt: `fan`, `number`, `select`, `button`, `expose`, `notify`. Bekannte Lücken der Erkennung:

- DPT 14.xxx (z. B. Leistung 14.056) wird nicht erkannt.
- DPT 1.018 (Präsenz) und 1.024 (Tag/Nacht) werden allein nicht als Binärsensor erkannt.
- Szenen ohne Nummer im Namen lassen sich nicht anlegen, weil Home Assistant `scene_number` braucht. Das Panel zeigt sie als *Nicht möglich*.
- Gruppenadressen werden immer dreistufig geschrieben (`1/2/3`), auch bei zweistufig oder frei adressierten Projekten.

Gruppenadressen, die zu keinem Typ passen, stehen im Panel unter *Ohne Typ*.

> [!TIP]
> Wird eine Entity mit dem falschen Typ erkannt, stell ihn im Panel um. Deine Wahl wird pro Entity gespeichert und bei jeder neuen Projektversion beibehalten.

## Wie die Entities erkannt werden

Jede Gruppenadresse landet in höchstens einer Entity. Die Schritte laufen in dieser Reihenfolge, und eine Gruppenadresse, die ein früherer Schritt verwendet hat, wird nicht noch einmal verwendet:

1. **Lichter**, aus fünf Quellen:
   1. Kanäle von Dimmaktoren (Schalt-, Dimm- und Helligkeitsobjekte eines Kanals)
   2. ETS-6-Funktionen (die Gruppenadressen einer Funktion)
   3. das Adressmuster `1/<Mitte>/<n>`: Mittelgruppe 1 = Schalten, 2 = Dimmen, 3 = Helligkeit, 4 = Helligkeit-Status, 5 = Status, zusammengefasst über dasselbe `<n>`
   4. Namen, die mit `LA<Nummer>` beginnen
   5. Namen, die auf ` s` (Schalten), ` d` (Dimmen), ` w` (Wert) oder ` status` enden

   Finden mehrere Quellen dieselbe Schalt-Adresse, werden sie zu einem Licht zusammengefasst. Es gewinnt die Quelle mit den meisten Feldern.
2. **Schalter:** DPT 1.001, gruppiert nach Namen. Ein Name mit *Status* wird zur Status-Adresse. Schaltausgänge von Dimmaktoren sind Lichter, keine Schalter. Adressen `1/7/x` werden übersprungen.
3. **Jalousien:** zuerst über die Kanäle von Jalousieaktoren, danach über Jalousie-Namen bei den übrigen Gruppenadressen.
4. **Klima:** pro Kanal eines Aktors oder Raumreglers.
5. **Wetter:** pro Wetterstation.
6. **Alles Übrige, eine Gruppenadresse nach der anderen:**
   1. `0/1/x` ist eine Szene.
   2. Ein Typ in eckigen Klammern im ETS-Namen gewinnt: `[switch]`, `[light]`, `[cover]`, `[sensor]`, `[binary_sensor]`, `[scene]`. Das gilt nur hier, für Gruppenadressen, die kein früherer Schritt verwendet hat.
   3. Sonst entscheidet der DPT, und bei mehrdeutigen DPTs der Name. Zum Beispiel ist 5.001 mit *Jalousie* im Namen eine Jalousie, mit *Helligkeit* ein Licht, sonst ein Sensor.
   4. Ohne DPT zählt nur der Name (*Licht*, *Lampe*, *Temp*, *Status*, …).
   5. Was übrig bleibt, landet unter *Ohne Typ*.

Beim *Übernehmen* kommen diese Regeln dazu:

1. **Deine Wahl im Panel gewinnt immer:** ausgewählt oder nicht, Name, Typ, korrigierte Adressen.
2. **Deine eigene KNX-YAML geht vor das Projekt.** Eine Entity mit derselben unique_id oder eine, die dieselbe Gruppenadresse verwendet (zum Beispiel die Temperatur deines eigenen Klimas), wird als *Eigene YAML* markiert und nicht doppelt angelegt. Du kannst sie in die App übernehmen oder jede Entity als *Schon vorhanden* markieren.
3. **Licht schlägt Schalter** auf derselben Gruppenadresse.
4. **DPT 16 wird eine Text-Entity**, außer sie wurde schon als Sensor übernommen.
5. Alles wird gegen das Schema der KNX-Integration geprüft. Ungültige Entities werden angezeigt und übersprungen.

## Projekt aktualisieren

Exportiere das Projekt erneut aus der ETS und lade es im Panel hoch (*Projektdatei hochladen*), oder lade es im KNX-Panel hoch und klicke auf *Aus KNX-Panel einlesen*. Das Panel zeigt, was sich ändert:

- **Geänderte** Entities, etwa mit neuem Namen oder einer zusätzlichen Status-Adresse, werden aktualisiert.
- **Entfernte** Entities werden gelöscht, oder behalten, wenn du das in den Einstellungen so eingestellt hast.
- **Neue** Entities werden *nicht* angelegt. Sie erscheinen als *Neu verfügbar*, und eine Benachrichtigung weist darauf hin.
- **Umadressierte** Gruppenadressen behalten ihre Entity: Sie wird vor dem Neuladen von KNX auf die neue unique_id umgezogen, sodass entity_id, Name, Bereich und Verlauf bleiben.

## Automatisierung

Die Aktion `knx_project_sync.import_project` führt einen Import ohne Panel aus:

```yaml
action: knx_project_sync.import_project
data:
  source: file              # oder knx_project
  file: knx/projekt.knxproj # relativ zum Konfigurationsordner
  password: !secret knx_project_password
  dry_run: true             # nur zurückgeben, was sich ändern würde
```

Sie gibt die Zusammenfassung zurück. Nach jedem Import wird das Ereignis `knx_project_sync_imported` ausgelöst.

## Deinstallation

1. *Einstellungen → Geräte & Dienste → KNX Project Sync → ⋮ → Löschen*.
2. In HACS: *KNX Project Sync* → ⋮ → *Entfernen*, danach Home Assistant neu starten.

Beim Löschen der Integration (Schritt 1):

| Was | Passiert |
|---|---|
| `packages/knx_project_sync.yaml` | wird gelöscht, KNX wird neu geladen |
| Erzeugte Entities | werden aus Home Assistant entfernt, auch aus der Entity-Registry. Der aufgezeichnete Verlauf bleibt in der Datenbank. |
| Paket-Zeile in der `configuration.yaml` | wird wieder entfernt, wenn die Integration sie eingetragen hat, mit Sicherung. Sie bleibt, wenn inzwischen andere Dateien in `packages/` liegen. |
| Ordner `packages/` | wird gelöscht, wenn die Integration ihn angelegt hat und er leer ist |
| `.storage/knx_project_sync`, Panel, Sensor *Letzter Import* | werden gelöscht |
| Bereiche | bleiben, weil andere Entities sie nutzen können |
| Sicherungen `*.knx_project_sync-*.bak` | bleiben, lösche sie von Hand |

> [!IMPORTANT]
> Entities, die du aus deiner eigenen YAML **in die App übernommen** hast, werden mit der Paket-Datei gelöscht. Willst du sie behalten, kopiere sie vor dem Löschen aus `packages/knx_project_sync.yaml` in deine eigene Konfiguration, oder spiel die Sicherung deiner Datei zurück (`<datei>.knx_project_sync-<zeit>.bak`).

## Fehlerbehebung

**Die Entities erscheinen nicht.**
Prüfe, ob die Paket-Zeile in der `configuration.yaml` steht. Das Panel und *Einstellungen → Reparaturen* bieten an, sie einzutragen. Danach unter *Einstellungen → System → Protokolle* nach Fehlern der KNX-Integration schauen.

**Eine Entity gibt es doppelt.**
Wahrscheinlich steht sie auch in deiner eigenen KNX-YAML, mit anderen Gruppenadressen. Markiere sie im Panel als *Schon vorhanden* oder übernimm sie in die App.

**Das Projekt lässt sich nicht lesen.**
Prüfe das Passwort. Projekte aus sehr alten ETS-Versionen unterstützt xknxproject eventuell nicht.

**Debug-Log**

```yaml
logger:
  logs:
    custom_components.knx_project_sync: debug
```

## Mithelfen

Hilfe ist willkommen, auch ohne Programmieren:

- **Falsche Erkennung melden:** Lege ein [Issue](https://github.com/badmintonroa/KNX_Project_Sync/issues) an, mit den Namen der Gruppenadressen, ihren DPTs und dem, was du erwartet hast. Bitte hänge deine `.knxproj` nicht an, sie enthält deine ganze Installation.
- **Fehler melden:** mit Version, den [Diagnosedaten](https://www.home-assistant.io/docs/configuration/troubleshooting/#download-diagnostics) der Integration und dem Debug-Log.
- **Übersetzungen:** Die Texte des Panels stehen in [`frontend/src/strings.ts`](frontend/src/strings.ts), der Rest in [`translations/`](custom_components/knx_project_sync/translations/).
- **Code:** Einrichtung, Tests und Release-Ablauf stehen in [CONTRIBUTING.md](CONTRIBUTING.md) (Englisch).

## Lizenz

[MIT](LICENSE). Die Entity-Erkennung basiert auf [knx2home](https://github.com/badmintonroa/knx2home).

Dies ist kein offizielles Projekt von Home Assistant oder der KNX Association. KNX und ETS sind Marken der KNX Association.
