# knx2home-ha-manifest v1

Das Manifest beschreibt **alle Home-Assistant-KNX-Entities, die aus einem ETS-Projekt entstehen**, und zwar so, dass ein späterer Import derselben (veränderten) ETS-Datei jede Entity wiedererkennt.

Es ist der Vertrag zwischen

- **knx2home** (TypeScript, Referenz-Implementierung): Die Golden-Files in `tests/fixtures/*.manifest.json` werden mit `tools/reference` aus dem unveränderten knx2home-Code erzeugt.
- **der HA-Integration** (Python, ab Schritt 3): Sie muss für dieselbe `.knxproj` dasselbe Manifest erzeugen (Parity-Tests). Sie speichert das Manifest des letzten Imports und vergleicht neue Importe damit (Schritt 5).

Das JSON-Schema liegt in [`schema/manifest-v1.schema.json`](../schema/manifest-v1.schema.json).

## Beispiel

```json
{
  "format": "knx2home-ha-manifest",
  "version": 1,
  "generator": { "name": "knx2home", "version": "0.1.0", "commit": "d4f0674…" },
  "project": { "name": "Musterhaus" },
  "options": { "drop_reserve": true },
  "entities": [
    {
      "key": "sensor:GA-12",
      "domain": "sensor",
      "name": "Wohnzimmer Temperatur",
      "config": { "name": "Wohnzimmer Temperatur", "state_address": "3/0/1", "type": "temperature" },
      "sources": [ { "field": "state_address", "address": "3/0/1", "ga_id": "GA-12" } ]
    }
  ],
  "unmapped": [
    { "address": "3/0/3", "ga_id": "GA-14", "name": "Flur Präsenz", "dpt": "1.018" }
  ]
}
```

## Felder

| Feld | Bedeutung |
|---|---|
| `format`, `version` | Fest `knx2home-ha-manifest` / `1`. Inkompatible Änderungen erhöhen `version`. |
| `generator` | Wer das Manifest erzeugt hat (`knx2home` oder später `knx_project_sync`), Version, optional Commit. Wird beim Vergleich ignoriert. |
| `project.name` | Projektname aus der ETS. |
| `options.drop_reserve` | GAs/Entities mit dem Namen „Reserve“ wurden verworfen (knx2home-Option `dropReserveFromUnknown`). |
| `entities[]` | Eine Entity pro Eintrag, siehe unten. |
| `unmapped[]` | GAs, für die knx2home keinen Entity-Typ gefunden hat (`_unknown`). Werden nicht in HA angelegt, aber in der Import-Vorschau angezeigt. |

### Entity

| Feld | Bedeutung |
|---|---|
| `key` | **Stabiler Schlüssel**, siehe nächster Abschnitt. Eindeutig im Manifest. |
| `domain` | HA-KNX-Plattform: `switch`, `binary_sensor`, `light`, `sensor`, `time`, `date`, `datetime`, `cover`, `scene`, `climate`, `weather`. |
| `name` | Entity-Name (= `config.name`), `null` falls keiner. |
| `config` | Der Eintrag für die `knx:`-YAML von Home Assistant, **genau so, wie knx2home ihn exportiert** (gleiche Felder und Werte wie im YAML-Export). |
| `sources[]` | Für jedes Adressfeld in `config` (`address`, `*_address`, `address_*`): Feldname, Gruppenadresse und deren ETS-Id. Reihenfolge = Reihenfolge in `config`. |

## Stabiler Schlüssel

```
<domain>:<GA-Id der Primäradresse>[#n]
```

- **ETS-Id statt Adresse:** Die GA-Id (`GA-12`, der Teil nach dem letzten `_` der ETS-Id `P-0A1B-0_GA-12`) bleibt erhalten, wenn eine GA in der ETS **umbenannt oder umadressiert** wird. Erst wenn die GA gelöscht und neu angelegt wird, entsteht ein neuer Schlüssel.
- **Primäradresse** pro Domain (das erste vorhandene Feld zählt):

  | Domain | Felder |
  |---|---|
  | switch, time, date, datetime, scene | `address` |
  | light | `address`, `brightness_address` |
  | binary_sensor, sensor | `state_address` |
  | cover | `move_long_address`, `position_address`, `move_short_address`, `stop_address` |
  | climate | `temperature_address`, `target_temperature_state_address` |
  | weather | `address_temperature` |

  Fehlt jedes dieser Felder, zählt das erste Adressfeld in `config`.
- **Fallback ohne GA-Id** (z. B. Adressen, die im Projekt gar nicht existieren): `<domain>:addr:<adresse>`.
- **Dubletten** (zwei Entities derselben Domain mit derselben Primär-GA, z. B. zwei Sensortypen auf einer GA) bekommen in Sortierreihenfolge `#2`, `#3`, …

Warum nicht Gerät/Kanal? xknxproject kennt die `DeviceInstance`-Id nicht, die physikalische Adresse ändert sich beim Umadressieren, und viele Entities (z. B. Taster-GAs ohne Aktor) haben keinen eindeutigen Kanal. Die GA-Id ist auf beiden Seiten verfügbar und in der Praxis am stabilsten. Beim Update-Abgleich (Schritt 5) dienen die übrigen `sources` als zusätzliche Hinweise, z. B. um eine neu angelegte GA mit gleicher Adresse wiederzuerkennen.

## Determinismus

- `entities` ist nach Domain sortiert (Reihenfolge der Tabelle oben, beginnend mit `switch`), innerhalb der Domain nach Primäradresse (numerisch) und dann nach `config`.
- `unmapped` ist nach Adresse sortiert.
- DPTs sind kanonisch (`9.001`, `1.018`, Hauptgruppe allein als `5`).
- Keine Zeitstempel. Zwei Läufe auf derselben Datei liefern dieselben Bytes (abgesehen von `generator`).

## Golden-Files neu erzeugen

```bash
# knx2home daneben auschecken und Abhängigkeiten installieren
git clone https://github.com/badmintonroa/knx2home ../knx2home && (cd ../knx2home && npm ci)

cd tools/reference
npm ci
KNX2HOME_DIR=../../../knx2home npm run generate
```

Danach `git diff tests/fixtures` prüfen: Jede Änderung ist eine Verhaltensänderung von knx2home, die der Python-Port nachziehen muss.
