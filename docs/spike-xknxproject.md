# Schritt 0: Machbarkeit xknxproject

> Historisch: Die Machbarkeitsprüfung ist abgeschlossen. `tools/spike/`, ihr Test und die `*.catalog.json`-Fixtures wurden entfernt; dass xknxproject die richtigen Daten liefert, prüft heute der Vergleich der fertigen Entities mit knx2home (`tests/test_mapping_parity.py`, CI-Job *real ETS projects*).

**Frage:** Liefert `xknxproject`, die Bibliothek, mit der die offizielle HA-KNX-Integration `.knxproj`-Dateien liest, alle Daten, die die Entity-Erkennung von knx2home braucht? Falls ja, wird nur die Mapping-Logik nach Python portiert, nicht der Parser (Option A).

**Ergebnis: Ja, Option A ist machbar.** xknxproject liefert alle benötigten Eingaben. Bei Overrides in der Applikation ist es sogar genauer als knx2home.

## Methode

1. `tools/fixtures/build_fixtures.py` erzeugt synthetische ETS6-Projekte. Sie sind klein, aber so aufgebaut wie echte Exporte: `knx_master.xml`, `Hardware.xml`, Applikationsprogramme mit `ComObjectRef`, Projekt mit `Links`.
2. `tools/reference` lässt den **unveränderten** knx2home-Code (`parseKnxproj` + `buildHaEntities`) darüber laufen und schreibt pro Fixture
   - `*.manifest.json`: die erkannten Entities (Golden-File, siehe [manifest-v1.md](manifest-v1.md)),
   - `*.catalog.json`: pro Gruppenadresse genau die Daten, die das Mapping verwendet: GA-Id, Adresse, Name, DPT und je verknüpftem Kommunikationsobjekt Gerät, Objekttext, Funktionstext, DPT und Flags.
3. `tools/spike/xknx_digest.py` baut dieselbe Sicht aus der xknxproject-Ausgabe. `tools/spike/compare.py` bzw. `tests/test_xknxproject_spike.py` vergleichen beide.

Geprüft mit **xknxproject 3.8.2**, der Version, die die aktuelle HA-KNX-Integration pinnt (HA 2026.2). Mit 3.10.0 ist das Ergebnis identisch.

## Ergebnisse

| Fixture | Inhalt | GAs | Ergebnis |
|---|---|---|---|
| `musterhaus_v1` | Schalt-, Dimm-, Jalousieaktor, Raumsensor, Taster, Zeitgeber | 18 | identisch |
| `musterhaus_v2` | v1 mit Umbenennungen, umadressierter GA, entferntem und neuem Gerät | 17 | identisch |
| `musterhaus_protected` | v1 als passwortgeschütztes ETS6-Projekt (AES) | 18 | identisch |
| `musterhaus_overrides` | v1 mit Texten/DPTs, die auf `ComObjectRef`/`ComObjectInstanceRef` überschrieben sind | 18 | 4 erwartete Abweichungen |
| `heuristics` (nachträglich, Schritt 3) | GA-Muster ohne Links, Heizungsregler, Wetterstation, Taster mit 1.011-Rückmeldung, Jalousiekanäle auf gemeinsamer GA | 46 | identisch |

### Erkenntnisse

1. **Alle Eingaben vorhanden.** GA-Id, Adresse, Name und DPT der GAs sowie die verknüpften Kommunikationsobjekte mit Gerät, Text, Funktionstext, DPT und R/W/T/U-Flags kommen aus xknxproject 1:1 so, wie knx2home sie verwendet. Auch die Reihenfolge der `Links` bleibt erhalten (erste GA = sendende GA).
2. **Overrides: xknxproject ist genauer.** knx2home liest Text, Funktionstext und DPT nur vom `ComObject` der Applikation. Overrides auf `ComObjectRef` (macht fast jede echte Applikation) und auf der Instanz (vom Anwender in der ETS geändert) ignoriert es. xknxproject löst sie so auf, wie die ETS sie anzeigt.
   - Auf die erkannten Entities wirkt sich das in diesem Fixture nicht aus (`musterhaus_overrides.manifest.json` = `musterhaus_v1.manifest.json`).
   - **Risiko für den Port:** knx2home gruppiert Objekte ohne ETS-Kanal über den Objekttext zu „Kanälen“. Mit den korrekten Texten aus xknxproject kann ein Statusobjekt in einem anderen „Kanal“ landen (Fixture: „Kanal A Rückmeldung“) und die Paarung Schalten/Status geht verloren.
   - **Entscheidung für Schritt 3:** Der Port verwendet die aufgelösten Werte aus xknxproject. Die Abweichungen sind in `*.deviations.json` dokumentiert, und der Parity-Test zeigt, ob sich daraus andere Entities ergeben. Falls ja, wird die Kanal-Gruppierung im Port robuster gemacht. Der Unterschied wird dann im Manifest-Vergleich als bewusste Verbesserung markiert.
3. **Passwortschutz** (ETS6, AES) funktioniert in beiden Implementierungen gleich, inklusive Fehler bei fehlendem oder falschem Passwort.
4. **Stabiler Schlüssel funktioniert.** Zwischen v1 und v2 behalten umbenannte GAs (`switch:GA-1`) und umadressierte GAs (`sensor:GA-12`, 3/0/1 → 3/1/1) ihren Schlüssel. Entfernte (`time:GA-16`, `date:GA-17`) und neue Entities (`sensor:GA-19`) werden erkannt.
5. **Bonus:** Die HA-KNX-Integration speichert ein im KNX-Panel hochgeladenes Projekt bereits als xknxproject-Ausgabe in `.storage/knx/knx_project.json`. Die Integration kann in Schritt 2 also zusätzlich anbieten, **das bereits in HA hochgeladene Projekt zu verwenden**, statt die Datei ein zweites Mal hochzuladen. Das funktioniert, sofern dort die vollständigen Kommunikationsobjekte enthalten sind, was in Schritt 2 noch zu prüfen ist.
6. **Version:** Die Integration darf keine eigene xknxproject-Version erzwingen, sondern nutzt die der KNX-Integration (`dependencies: ["knx"]`). Der Port muss daher mit dem jeweils von HA gepinnten Stand laufen. Die CI testet gegen genau diese Version.

### Verhalten von knx2home, das der Port übernimmt (oder bewusst ändert)

Das sind Beobachtungen aus den Golden-Files, kein Fehler im Spike. Es sind mögliche Verbesserungen für später:

- Ein rein lesendes 1-Bit-Objekt mit DPT 1.018 („Flur Präsenz“) landet in `unmapped` statt als `binary_sensor`.
- GAs namens „Reserve“ werden verworfen (`drop_reserve`).
- `time`/`date` setzen `address` und `state_address` auf dieselbe GA.
- `buildHaEntities` hat zwei Pfade: strukturiertes Mapping über Geräte/Kanäle (`map.ts`) und, falls es nichts findet, die Aggregat-Heuristiken (`aggregate.ts`). Für die ETS6-Fixtures greift der Aggregat-Pfad. Der Port braucht beide.

## Nachträglich geprüft mit echten Projekten

ETS4, ETS5 mit Modulen, ETS6-Funktionen/Smart Linking sowie zweistufige und freie Adressierung sind inzwischen mit den echten Testprojekten von xknxproject abgedeckt (CI-Job „real ETS projects“, Ergebnis in [port-notes.md](port-notes.md)). Offen bleibt die Performance bei großen Projekten. Das Parsen läuft im Executor und blockiert den HA-Event-Loop nicht.

## Reproduzieren

```bash
pip install -r requirements_test.txt
python tools/spike/compare.py   # Übersicht
pytest                          # alle Prüfungen
```
