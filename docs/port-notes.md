# Schritt 3: Python-Port der knx2home-Erkennung

Der Port liegt in [`custom_components/knx2home_importer/mapping/`](../custom_components/knx2home_importer/mapping/). Er ist reines Python ohne Home-Assistant-Abhängigkeit.

| Modul | knx2home-Vorlage |
|---|---|
| `catalog.py` | xknxproject-Ausgabe → `group_addresses` + Links (entspricht dem Teil von `parse.ts`, den das Mapping nutzt) |
| `dpt.py` | `utils.ts` (`normalizeDptToDot`, `normalizeDptToHyphen`) |
| `heuristics.py` | `heuristics.ts`, `utils.isSceneLikeName` |
| `aggregate.py` | `aggregate.ts` |
| `entities.py` | `export.ts` → `buildHaEntities` (Aggregat-Pfad) |
| `manifest.py` | `tools/reference/generate.ts` + unique_ids der HA-KNX-Integration |

**Parity:** `tests/test_mapping_parity.py` vergleicht für jedes Fixture das Manifest des Ports mit dem Golden-File von knx2home, also Entities, Schlüssel und nicht zugeordnete GAs. Alle Fixtures stimmen exakt überein, auch `heuristics`. Dieses Fixture deckt Licht nach Adress- und Namensmuster, Jalousien nach Namen, Klima, Wetterstation, Taster-Rückmeldung (1.011), Szenen, Einzel-GA-Fallbacks und „Reserve“ ab.

## Bewusste Unterschiede und Grenzen

1. **Nur der Aggregat-Pfad.** `buildHaEntities` nutzt zuerst das strukturierte Mapping aus `map.ts` und fällt nur dann auf die Aggregate zurück, wenn es nichts findet. Bei ETS-5.7+/6-Projekten (`Links`-Attribut) liefert das strukturierte Mapping praktisch nie etwas. Es springt nur an, wenn in der ETS an einzelnen Objekten Flags überschrieben wurden, und ersetzt dann die Erkennung des *ganzen* Projekts. Das ist ein Zufallseffekt, der sich mit xknxproject auch nicht nachbilden lässt, weil die Flags dort schon zusammengeführt sind. Der Port verwendet immer den Aggregat-Pfad.
2. **ETS4 / ETS5 < 5.7** (`Connectors`): knx2home erzeugt dort Links mit `origin: "groupAddressRef"` und Rollen. xknxproject liefert für diese Projekte dieselben Links wie für ETS6 (sendende GA zuerst). Die Zweige von knx2home, die nur mit solchen Links laufen (`buildLinkedLightAggregates`, Link-Ergänzungen bei Schaltern und Jalousien), sind daher nicht portiert. Für ältere Projekte ist das Ergebnis gleichwertig, aber nicht garantiert identisch.
3. **Overrides auf ComObjectRef/Instanz** werden wie in der ETS aufgelöst (siehe [spike-xknxproject.md](spike-xknxproject.md)). knx2home ignoriert sie.
4. **GA ohne DPT:** Der Port übernimmt den DPT des ersten verknüpften Kommunikationsobjekts, knx2home nur einen DPT, der direkt an der Objekt-Instanz steht.
5. **Regex-Semantik:** knx2home nutzt JavaScript-Regexe ohne `u`-Flag. `\b`, `\w` und `\d` kennen dort nur ASCII. `mapping/jsre.py` bildet das nach (`re.ASCII`), und `replace` ohne `g` ersetzt nur den ersten Treffer.
6. **Sortierung bei Gleichstand:** Haben zwei Entities derselben Domain dieselbe Primäradresse, sortiert knx2home per `localeCompare`, der Port nach Codepoints. Das betrifft nur die Reihenfolge der `#2`-Schlüssel solcher Dubletten.

## Gefundene Schwächen von knx2home

Sie bleiben im Manifest erhalten, damit die Parity bestehen bleibt. Die Integration behandelt sie beim Import (siehe [import.md](import.md)):

- **Licht und Schalter auf derselben GA:** Lichter aus Adress- oder Namensmustern (z. B. `1/1/10` + `1/3/10`) unterdrücken den Schalter auf derselben GA nicht, das tun nur Lichter aus Dimmkanälen. Die Integration übernimmt in diesem Fall nur das Licht.
- **Szenen ohne Nummer:** Ohne Zahl im Namen fehlt `scene_number`, das HA aber verlangt. Solche Szenen werden beim Import als ungültig angezeigt und nicht angelegt.
- **1.018 (Präsenz) und 1.024 (Tag/Nacht)** als reine Lese-Objekte landen in `unmapped` statt als `binary_sensor`.
- **14.xxx** (z. B. Leistung 14.056) ist nicht in der Sensortabelle und landet in `unmapped`.
