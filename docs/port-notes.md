# Schritt 3: Python-Port der knx2home-Erkennung

Der Port liegt in [`custom_components/knx_project_sync/mapping/`](../custom_components/knx_project_sync/mapping/). Er ist reines Python ohne Home-Assistant-Abhängigkeit.

| Modul | knx2home-Vorlage |
|---|---|
| `catalog.py` | xknxproject-Ausgabe → `group_addresses` + Links (entspricht dem Teil von `parse.ts`, den das Mapping nutzt) |
| `dpt.py` | `utils.ts` (`normalizeDptToDot`, `normalizeDptToHyphen`) |
| `heuristics.py` | `heuristics.ts`, `utils.isSceneLikeName` |
| `aggregate.py` | `aggregate.ts` |
| `entities.py` | `export.ts` → `buildHaEntities` (Aggregat-Pfad) |
| `manifest.py` | `tools/reference/generate.ts` + unique_ids der HA-KNX-Integration |

**Parity:** `tests/test_mapping_parity.py` vergleicht für jedes Fixture das Manifest des Ports mit dem Golden-File von knx2home, also Entities, Schlüssel und nicht zugeordnete GAs. Alle Fixtures stimmen exakt überein, auch `heuristics`. Dieses Fixture deckt Licht nach Adress- und Namensmuster, Jalousien nach Namen, Klima, Wetterstation, Taster-Rückmeldung (1.011), Szenen, Einzel-GA-Fallbacks und „Reserve“ ab.

**Echte ETS-Projekte:** Die CI (Job „real ETS projects“) vergleicht den Port zusätzlich auf den 9 Testprojekten von xknxproject mit knx2home: ETS4 (mit und ohne Passwort), ETS5 (inkl. Modulen), ETS6 (Funktionen, Smart Linking, zwei­stufige und freie Adressierung). 8 von 9 Projekten stimmen exakt überein. Beim neunten legt der Port 3 Sensoren zusätzlich an (Punkt 4 unten). Die Projekte stehen unter GPL-2.0 und liegen deshalb nicht im Repo, die CI holt sie von einem festen xknxproject-Commit.

## Bewusste Unterschiede und Grenzen

1. **Nur der Aggregat-Pfad.** `buildHaEntities` nutzt zuerst das strukturierte Mapping aus `map.ts` und fällt nur dann auf die Aggregate zurück, wenn es nichts findet. Bei ETS-5.7+/6-Projekten (`Links`-Attribut) liefert das strukturierte Mapping praktisch nie etwas. Es springt nur an, wenn in der ETS an einzelnen Objekten Flags überschrieben wurden, und ersetzt dann die Erkennung des *ganzen* Projekts. Das ist ein Zufallseffekt, der sich mit xknxproject auch nicht nachbilden lässt, weil die Flags dort schon zusammengeführt sind. Der Port verwendet immer den Aggregat-Pfad.
2. **ETS6-Funktionen** (`GroupAddressRef` in Räumen/Funktionen, auch per Smart Linking) sind in knx2home Links mit `origin: "groupAddressRef"`. Der Port übernimmt sie aus `xknxproject["functions"]` als Kontext pro Funktion (`Catalog.function_context`) und portiert die Zweige, die damit arbeiten: `buildLinkedLightAggregates`, die Status-Ergänzung bei Schaltern und Jalousien. knx2home macht dabei aus *jeder* Funktion mit 1-Bit-GA ein Licht, auch aus Schalt-Funktionen, und der Port übernimmt das. Zusammen mit dem Schalter derselben GA wird beim Import nur das Licht angelegt.
3. **Overrides auf ComObjectRef/Instanz** werden wie in der ETS aufgelöst (siehe [spike-xknxproject.md](spike-xknxproject.md)). knx2home ignoriert sie.
4. **GA ohne DPT:** Der Port übernimmt den (ersten) DPT des ersten verknüpften Kommunikationsobjekts. knx2home übernimmt nur einen DPT, der direkt an der Objekt-Instanz steht, und kann Listen wie `DPST-9-1 DPST-9-2 …` nicht lesen. Folge (`xknx_test_project`): Der Port legt für solche GAs 2-Byte-Float-Sensoren an, knx2home verwirft sie.
5. **Adressformat:** Wie knx2home schreibt der Port Gruppenadressen immer dreistufig (`0/4/1`), auch bei zweistufig oder frei adressierten Projekten. Hinweis: Lädt man ein solches Projekt zusätzlich ins KNX-Panel, formatiert HA die unique_ids im Projektformat. Das betrifft nur zwei­stufige und freie Projekte.
6. **Regex-Semantik:** knx2home nutzt JavaScript-Regexe ohne `u`-Flag. `\b`, `\w` und `\d` kennen dort nur ASCII. `mapping/jsre.py` bildet das nach (`re.ASCII`), und `replace` ohne `g` ersetzt nur den ersten Treffer.
7. **Sortierung bei Gleichstand:** Haben zwei Entities derselben Domain dieselbe Primäradresse, sortiert knx2home per `localeCompare`, der Port nach Codepoints. Das betrifft nur die Reihenfolge der `#2`-Schlüssel solcher Dubletten.

## Gefundene Schwächen von knx2home

Sie bleiben im Manifest erhalten, damit die Parity bestehen bleibt. Die Integration behandelt sie beim Import (siehe [import.md](import.md)):

- **Licht und Schalter auf derselben GA:** Lichter aus Adress- oder Namensmustern (z. B. `1/1/10` + `1/3/10`) unterdrücken den Schalter auf derselben GA nicht, das tun nur Lichter aus Dimmkanälen. Die Integration übernimmt in diesem Fall nur das Licht.
- **Szenen ohne Nummer:** Ohne Zahl im Namen fehlt `scene_number`, das HA aber verlangt. Solche Szenen werden beim Import als ungültig angezeigt und nicht angelegt.
- **1.018 (Präsenz) und 1.024 (Tag/Nacht)** als reine Lese-Objekte landen in `unmapped` statt als `binary_sensor`.
- **14.xxx** (z. B. Leistung 14.056) ist nicht in der Sensortabelle und landet in `unmapped`.
