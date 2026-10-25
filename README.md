# KNX Project Sync

Home-Assistant-Integration (HACS), die aus einer ETS-Projektdatei (`.knxproj`) automatisch die KNX-Entities anlegt und sie beim Hochladen einer geänderten Datei aktualisiert. Dabei bleiben entity_ids, Namen, Bereiche und der Verlauf erhalten.

Die Entity-Erkennung stammt aus [knx2home](https://github.com/badmintonroa/knx2home). Die Integration enthält einen Python-Port davon, der per Tests exakt gleiche Ergebnisse liefert. Die ETS-Datei wird mit [xknxproject](https://github.com/XKNX/xknxproject) gelesen, derselben Bibliothek, die die offizielle KNX-Integration verwendet. Passwortgeschützte Projekte werden unterstützt.

## Installation

1. HACS → *Integrationen* → ⋮ → *Benutzerdefinierte Repositories* → `https://github.com/badmintonroa/Knx-has-auto-importer`, Typ *Integration*. Danach „KNX Project Sync“ installieren und HA neu starten.
2. In der `configuration.yaml` Pakete aktivieren (falls noch nicht geschehen) und HA neu starten:

   ```yaml
   homeassistant:
     packages: !include_dir_named packages
   ```

3. *Einstellungen → Geräte & Dienste → Integration hinzufügen → KNX Project Sync*. Voraussetzung ist eine eingerichtete KNX-Integration.

### Umstieg von „KNX2HOME Importer“ (0.1.0)

Die Integration hieß bis 0.1.0 „KNX2HOME Importer“ (`knx2home_importer`). Nach dem Update in HACS „KNX Project Sync“ hinzufügen: Die bisherige Installation wird erkannt und mit allen Entities, Einstellungen und dem Import-Stand übernommen, `packages/knx2home_importer.yaml` wird zu `packages/knx_project_sync.yaml`. Danach den alten Eintrag löschen (ein Repair-Hinweis erinnert daran). entity_ids, Namen, Bereiche und Verlauf bleiben erhalten.

## Benutzung

- **Erster Import:** `.knxproj` hochladen (oder das schon im KNX-Panel hochgeladene Projekt wählen), Entity-Typen wählen, Vorschau prüfen, absenden. Alle erkannten Entities landen in `packages/knx_project_sync.yaml`, und KNX wird neu geladen.
- **Panel „KNX Project Sync“ (Seitenleiste, nur Admins):** Liste aller erkannten Entities, gruppiert nach ETS-Raum oder Typ, mit Suche und Filtern. Pro Entity: anlegen ja/nein, umbenennen, falsche Gruppenadressen korrigieren, Schalter ↔ Licht umstellen (bei Schaltern mit „Licht“, „Lampe“ usw. im Namen schlägt das Panel *Als Licht?* vor). Änderungen sind ein Entwurf, bis du auf *Übernehmen* klickst.
- **Update:** Im Panel eine neue Projektdatei hochladen oder das Projekt aus dem KNX-Panel einlesen (alternativ bei der Integration *Konfigurieren*). Geänderte und entfernte Entities werden nachgezogen. **Neue Entities werden nicht automatisch angelegt**, sondern erscheinen als „Neu verfügbar“, und eine Benachrichtigung weist darauf hin.
- **Eigene KNX-YAML:** Entities, die du schon von Hand angelegt hast (gleiche Gruppenadresse, auch Schalter ↔ Licht), werden erkannt und nicht doppelt angelegt. Im Panel kannst du sie per *In App übernehmen* in die App verschieben, mit Sicherung deiner Datei, oder beliebige Entities als *Schon vorhanden* markieren.
- **Automatisierbar:** Service `knx_project_sync.import_project` (mit `dry_run`).

Details: [docs/import.md](docs/import.md)

## Status

| Schritt | Inhalt | |
|---|---|---|
| 0 | Machbarkeit xknxproject → [docs/spike-xknxproject.md](docs/spike-xknxproject.md) | ✅ |
| 1 | Manifest-Vertrag + Golden-Files aus knx2home → [docs/manifest-v1.md](docs/manifest-v1.md) | ✅ |
| 2 | Integration: HACS, Config-/Options-Flow mit Upload, Passwort, KNX-Panel-Projekt | ✅ |
| 3 | Python-Port der Erkennung, Parity mit knx2home → [docs/port-notes.md](docs/port-notes.md) | ✅ |
| 4 | Paket-YAML, Prüfung gegen das KNX-Schema, `knx.reload`, Konflikte mit eigener YAML | ✅ |
| 5 | Update: Diff-Vorschau, unique_id-Migration, Löschen/Behalten, Service | ✅ |
| 6 | Diagnose, Sensor „Letzter Import“, ETS-Räume → Bereiche, Repair-Hinweise | ✅ |
| 7 | CI: pytest, ruff, hassfest, HACS-Validierung, knx2home-Golden-Check | ✅ |
| 8 | Panel: Auswahl, Umbenennen, Schalter ↔ Licht, neue Entities nur vorschlagen | ✅ |

## Aufbau

```
custom_components/knx_project_sync/
  mapping/          Port der knx2home-Erkennung (reines Python)
  plan.py           Diff zwischen Projekt und letztem Import
  importer.py       Parsen, Planen, Anwenden (YAML, Reload, Registry, Bereiche)
  writer.py         Paket-Datei, unique_ids aus YAML
  config_flow.py    Einrichtung und erneuter Import
  websocket.py      API und Registrierung des Panels
  frontend/         gebündeltes Panel (Quelltext in /frontend)
  migration.py      Übernahme einer Installation als „KNX2HOME Importer“
  sensor.py, diagnostics.py, services.yaml, strings.json, translations/
schema/             JSON-Schema des Manifests
docs/               Spike, Manifest, Port-Notizen, Import
tests/              pytest (Port, Plan, HA-Integration), Fixtures + Golden-Files
frontend/           Panel (Lit, TypeScript): npm run build / check / test
tools/              Fixture-Generator, knx2home-Referenzgenerator, xknxproject-Vergleich
```

## Entwicklung

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements_test.txt
pytest
ruff check custom_components tests tools/spike tools/fixtures
```

Fixtures neu erzeugen: `python tools/fixtures/build_fixtures.py`. Golden-Files aus knx2home neu erzeugen (knx2home liegt in `../knx2home`):

```bash
(cd ../knx2home && npm ci)
cd tools/reference && npm ci && npm run generate
```

Die CI erzeugt die Golden-Files bei jedem Lauf und wöchentlich mit dem aktuellen knx2home-`main` neu. Ändert knx2home sein Verhalten, schlägt sie fehl, und der Port muss nachziehen.
