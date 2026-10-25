# KNX HA Auto Importer

Home-Assistant-Integration (HACS), die aus einer ETS-Projektdatei (`.knxproj`) automatisch die KNX-Entities anlegt und sie beim Hochladen einer geänderten Datei aktualisiert, ohne Entity-IDs, Namen, Bereiche oder den Verlauf zu verlieren.

Die Entity-Erkennung (welche Gruppenadressen bilden ein Licht, eine Jalousie, einen Sensor, …) stammt aus [knx2home](https://github.com/badmintonroa/knx2home). knx2home dient als **Referenz-Implementierung**. Die Integration portiert die Logik nach Python und liest die ETS-Datei mit [xknxproject](https://github.com/XKNX/xknxproject), derselben Bibliothek, die die offizielle HA-KNX-Integration verwendet.

## Status

| Schritt | Inhalt | Stand |
|---|---|---|
| 0 | Machbarkeit xknxproject → [docs/spike-xknxproject.md](docs/spike-xknxproject.md) | ✅ machbar |
| 1 | Manifest-Vertrag + Golden-Files aus knx2home → [docs/manifest-v1.md](docs/manifest-v1.md) | ✅ |
| 2 | Gerüst der Integration (HACS, Config-Flow mit Upload + Passwort) | offen |
| 3 | Python-Port des Mappings, Parity-Tests gegen die Golden-Files | offen |
| 4 | YAML-Paket schreiben + `knx.reload` | offen |
| 5 | Update-Flow: Diff-Vorschau, Registry-Migration | offen |
| 6 | Komfort: Diagnose, Status-Sensor, Bereiche aus ETS | offen |

## Aufbau

```
schema/manifest-v1.schema.json   JSON-Schema des Manifests
docs/                            Spike-Ergebnis, Manifest-Spezifikation
tests/fixtures/                  synthetische ETS6-Projekte + Golden-Files
  <name>.knxproj                 Projektdatei (erzeugt von tools/fixtures)
  <name>.manifest.json           erkannte Entities laut knx2home (Golden-File)
  <name>.catalog.json            Projektdaten laut knx2home, für den xknxproject-Vergleich
  <name>.deviations.json         dokumentierte, erwartete Abweichungen
  passwords.json                 Passwörter der geschützten Fixtures
tools/fixtures/build_fixtures.py erzeugt die .knxproj-Fixtures
tools/reference/                 erzeugt die Golden-Files mit dem knx2home-Code (Node)
tools/spike/                     xknxproject-Sicht auf ein Projekt + Vergleich
```

## Entwicklung

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements_test.txt
pytest
```

Fixtures neu erzeugen (nach Änderungen an `build_fixtures.py`):

```bash
python tools/fixtures/build_fixtures.py
```

Golden-Files neu erzeugen (nach Änderungen an Fixtures oder knx2home), knx2home liegt daneben in `../knx2home`:

```bash
(cd ../knx2home && npm ci)
cd tools/reference && npm ci && npm run generate
```

Die CI erzeugt die Golden-Files bei jedem Lauf und wöchentlich mit dem aktuellen knx2home-`main` neu und schlägt fehl, wenn sich das Verhalten von knx2home geändert hat.
